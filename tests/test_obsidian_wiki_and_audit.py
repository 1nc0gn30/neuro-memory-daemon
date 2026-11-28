"""Self-contained tests for Obsidian Second Brain Wiki, Audit, Sync, Bases, Daily, Backlinks, Bundle, Notes & Vaelor REST/MCP endpoints.

Uses an isolated tmp_path vault fixture via monkeypatch(HOME) so 0 tests skip in CI
and the host's live Obsidian Vault is never read or mutated.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Generator

import pytest

from neuro_memory_daemon import MemoryDaemon
from neuro_memory_daemon.mcp_server import MCPServer
from neuro_memory_daemon.ui_server import MemoryUIServer, start_server_in_thread, _parse_wiki_article
from tests.test_ui_server import get_free_port, _http_get, _http_post


def _populate_fixture_vault(vault_dir: Path) -> None:
    """Create a realistic, self-contained Obsidian Vault fixture inside tmp_path."""
    (vault_dir / "06-Wiki").mkdir(parents=True, exist_ok=True)
    (vault_dir / "05-Telemetry").mkdir(parents=True, exist_ok=True)
    (vault_dir / "04-Ingested").mkdir(parents=True, exist_ok=True)
    (vault_dir / "07-Daily").mkdir(parents=True, exist_ok=True)
    (vault_dir / "Studio" / "Tools").mkdir(parents=True, exist_ok=True)

    # 1. Create 14 valid JSON Canvas 1.0 files
    canvas_names = [
        "Vaelor Layer-1 Complete Architecture.canvas",
        "Zoth Second Brain.canvas",
        "Vaelor & Sovereign Economy.canvas",
        "Zoth Plugin & Connector Marketplace.canvas",
        "Zoth 6 Mathematical Pillars.canvas",
        "Zoth Autonomous Agents & Hermes Fleet.canvas",
        "Netrunner Cyber-Cortex Knowledge Map.canvas",
        "ZothOS & Studio Supply-Chain Trust Stack.canvas",
        "Zoth MCP Hub Architecture.canvas",
        "Zoth Obsidian Graph Map.canvas",
        "Zoth Security Hardening Map.canvas",
        "Zoth Memory Consolidation Map.canvas",
        "Zoth Local Inference Map.canvas",
        "Zoth Storage WAL Map.canvas",
    ]
    for idx, cname in enumerate(canvas_names):
        cdata = {
            "nodes": [
                {"id": f"n{idx}_0", "type": "group", "label": cname[:-7], "x": 0, "y": 0, "width": 500, "height": 300},
                {"id": f"n{idx}_1", "type": "text", "text": f"## {cname[:-7]}\nLinked to [[00 Home]] and [[Zoth OS]].", "x": 20, "y": 20, "width": 300, "height": 160},
            ],
            "edges": [
                {"id": f"e{idx}_0", "fromNode": f"n{idx}_0", "toNode": f"n{idx}_1", "label": "contains"},
            ],
        }
        (vault_dir / cname).write_text(json.dumps(cdata, indent=2), encoding="utf-8")

    # 2. Create 18 valid Obsidian Bases YAML files
    base_specs = [
        ("Zoth 72 Sovereign Tools.base", 'filters:\n  and:\n    - file.inFolder("Studio/Tools")\nformulas:\n  status_badge: status\n  pillar_label: pillar\nproperties:\n  title:\n    displayName: Tool\n  category:\n    displayName: Category\n  pillar:\n    displayName: Pillar\n  formula.status_badge:\n    displayName: Status\n  file.name:\n    displayName: Note\nviews:\n  - type: table\n    name: Tools Table\n    order:\n      - file.name\n      - title\n      - category\n      - pillar\n      - formula.status_badge\n'),
        ("Zoth Fleet & Daemons.base", 'filters:\n  and:\n    - file.hasTag("daemon")\nviews:\n  - type: table\n    name: Fleet\n'),
        ("Zoth LLM Wiki Index.base", 'filters:\n  and:\n    - file.inFolder("06-Wiki")\nviews:\n  - type: table\n    name: Wiki Index\n'),
        ("Zoth Memory Stratum.base", 'views:\n  - type: table\n    name: Memory Stratum\n'),
        ("Zoth Autonomous Agents.base", 'views:\n  - type: table\n    name: Agents\n'),
        ("Vaelor Ecosystem & Patronage Ledger.base", 'views:\n  - type: table\n    name: Vaelor\n'),
        ("Sovereign MCP Tools & Agent Catalog.base", 'views:\n  - type: table\n    name: MCP Catalog\n'),
    ]
    for i in range(11):
        base_specs.append((f"Zoth Auxiliary Index {i + 1}.base", f'views:\n  - type: table\n    name: Aux {i + 1}\n'))
    for bname, byaml in base_specs:
        (vault_dir / bname).write_text(byaml, encoding="utf-8")

    # 3. Create 10 Karpathy LLM Wiki notes in 06-Wiki/
    wiki_titles = [
        "Vaelor Account-Lattice & PoUW Protocol",
        "Biomorphic STDP & 3D Netrunner Cortex",
        "Neuro-Memory 21-Tool MCP Server & Agent Connector Protocol",
        "Obsidian Second Brain Architecture",
        "Hermes Agent Fleet Protocol",
        "ZothOS Hardening & SquashFS",
        "SQLite WAL Concurrency Guide",
        "CA3 Pattern Completion Dynamics",
        "Ebbinghaus Consolidation Curves",
        "Zero-Egress Loopback Security",
    ]
    for idx, title in enumerate(wiki_titles):
        wcontent = f"""---
title: "{title}"
created: "2026-10-26T02:00:00Z"
updated: "2026-11-28T09:00:00Z"
confidence: 0.99
stdp_engrams: {20 + idx}
status: "CANONICAL"
category: "LLM-Wiki"
tags: [wiki, canonical, vaelor, stdp]
---

# {title}

> [!abstract] Executive Summary
> Canonical wiki synthesis for **{title}** covering Vaelor, STDP, and [[00 Home]] integration.

## Overview
Connected to [[00 Home]], [[Zoth OS]], and [[Zoth Memory]]. Plaintext Zoth OS reference.
"""
        (vault_dir / "06-Wiki" / f"{title}.md").write_text(wcontent, encoding="utf-8")

    # 4. Create 72 Studio Tool notes (linked to 00 Home & Zoth OS)
    tool_links = []
    for i in range(1, 73):
        tname = f"Studio tool-{i:02d}"
        tool_links.append(f"[[{tname}]]")
        extra_unlinked = "Plaintext mention of Zoth OS architecture." if i <= 8 else ""
        tcontent = f"""---
title: "Tool {i:02d}"
category: "AI & Agents"
pillar: "Pillar I"
status: "active"
tags: [zoth-studio, tool]
---

# Tool {i:02d}

Linked back to [[00 Home]] and [[Zoth OS]] and [[Zoth Memory]]. {extra_unlinked}
"""
        (vault_dir / "Studio" / "Tools" / f"{tname}.md").write_text(tcontent, encoding="utf-8")

    # 4b. Create 6 ingested notes with plaintext Zoth OS mentions (no [[Zoth OS]] link) for unlinked-mention coverage
    for i in range(1, 7):
        (vault_dir / "04-Ingested" / f"unlinked-mention-{i}.md").write_text(
            f"---\ntitle: \"Unlinked Mention {i}\"\ntags: [ingested]\n---\n\n# Note {i}\n\nMentions Zoth OS in plaintext and links to [[00 Home]].\n",
            encoding="utf-8",
        )

    # 5. Create core hub notes: 00 Home.md, Zoth OS.md, Zoth Memory.md
    home_content = f"""---
title: "00 Home"
tags: [moc, hub, second-brain]
---

# 00 Home

Central hub for the Obsidian Second Brain Vault, Vaelor Network, and Neuro-Memory Daemon.
Links to [[Zoth OS]], [[Zoth Memory]], [[06-Wiki/Vaelor Account-Lattice & PoUW Protocol]], and all tools:
{" · ".join(tool_links)}
"""
    (vault_dir / "00 Home.md").write_text(home_content, encoding="utf-8")

    (vault_dir / "Zoth OS.md").write_text(
        "---\ntitle: \"Zoth OS\"\ntags: [os, moc]\n---\n\n# Zoth OS\n\nSovereign Linux distribution linked to [[00 Home]] and [[Zoth Memory]].\n",
        encoding="utf-8",
    )
    (vault_dir / "Zoth Memory.md").write_text(
        "---\ntitle: \"Zoth Memory\"\ntags: [memory, moc]\n---\n\n# Zoth Memory\n\nSTDP Memory Substrate linked to [[00 Home]] and [[Zoth OS]].\n",
        encoding="utf-8",
    )

    # 6. Create 3 Telemetry notes + portable bundle JSON in 05-Telemetry/
    for ttitle in (
        "Neuro-Memory Cortex Telemetry",
        "Vaelor Live Ledger Telemetry",
        "Zoth Fleet Health Telemetry",
    ):
        (vault_dir / "05-Telemetry" / f"{ttitle}.md").write_text(
            f"---\ntitle: \"{ttitle}\"\ntags: [telemetry]\n---\n\n# {ttitle}\n\nLinked to [[00 Home]] and [[Zoth OS]].\n",
            encoding="utf-8",
        )

    bundle_payload = {
        "ok": True,
        "version": "1.0.0",
        "healthScore": 100,
        "auditMetrics": {
            "totalNotes": 88,
            "canvasesCount": len(canvas_names),
            "basesCount": len(base_specs),
            "wikiCount": len(wiki_titles),
        },
        "wikiCount": len(wiki_titles),
        "canvasesCount": len(canvas_names),
        "basesCount": len(base_specs),
        "wikiArticles": wiki_titles,
        "canvases": canvas_names,
        "bases": [b[0] for b in base_specs],
        "topHubs": [
            {"title": "00 Home", "relPath": "00 Home.md", "inDegree": 80, "outDegree": 75, "totalDegree": 155, "cluster": "Root"},
            {"title": "Zoth OS", "relPath": "Zoth OS.md", "inDegree": 80, "outDegree": 2, "totalDegree": 82, "cluster": "Root"},
            {"title": "Zoth Memory", "relPath": "Zoth Memory.md", "inDegree": 75, "outDegree": 2, "totalDegree": 77, "cluster": "Root"},
            {"title": "Vaelor Account-Lattice & PoUW Protocol", "relPath": "06-Wiki/Vaelor Account-Lattice & PoUW Protocol.md", "inDegree": 2, "outDegree": 3, "totalDegree": 5, "cluster": "Wiki"},
            {"title": "Biomorphic STDP & 3D Netrunner Cortex", "relPath": "06-Wiki/Biomorphic STDP & 3D Netrunner Cortex.md", "inDegree": 1, "outDegree": 3, "totalDegree": 4, "cluster": "Wiki"},
        ],
        "dailyNote": "07-Daily/2026-11-28.md",
    }
    digest = hashlib.sha256(json.dumps(bundle_payload, sort_keys=True).encode("utf-8")).hexdigest()
    bundle_payload["bundleSha256"] = digest
    (vault_dir / "05-Telemetry" / "second_brain_bundle.json").write_text(
        json.dumps(bundle_payload, indent=2), encoding="utf-8"
    )


@pytest.fixture
def obsidian_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[tuple[MemoryUIServer, str, MemoryDaemon], None, None]:
    """Start an ephemeral test server backed by a self-contained tmp_path Obsidian Vault."""
    fake_home = tmp_path / "home"
    vault_dir = fake_home / "Documents" / "Obsidian Vault"
    _populate_fixture_vault(vault_dir)
    monkeypatch.setenv("HOME", str(fake_home))

    port = get_free_port()
    db_file = tmp_path / "obsidian_test_db.db"
    daemon = MemoryDaemon(db_path=db_file)

    pub_dir = Path(__file__).resolve().parent.parent / "public"
    server = start_server_in_thread(
        host="127.0.0.1",
        port=port,
        daemon=daemon,
        public_dir=pub_dir,
    )
    base_url = f"http://127.0.0.1:{port}"

    yield server, base_url, daemon

    server.stop()


def test_parse_wiki_article_unit(tmp_path: Path):
    """Test unit parsing of Obsidian Flavored Markdown with YAML frontmatter & callout."""
    wiki_file = tmp_path / "Test Article.md"
    content = """---
title: "Test Architecture Article"
created: 2026-10-26T02:00:00Z
updated: 2026-10-26T02:30:00Z
confidence: 0.98
stdp_engrams: 42
status: CANONICAL
category: Architecture
tags: [test, architecture, zothos]
---

> [!abstract] Executive Summary
> This is a test executive summary synthesized by Karpathy LLM Wiki engine.
> It tests multi-line callout extraction.

## Core Pillars
Here is the body content with [[Internal Wikilink]].
"""
    wiki_file.write_text(content, encoding="utf-8")

    article = _parse_wiki_article(wiki_file)
    assert article["title"] == "Test Architecture Article"
    assert article["created"] == "2026-10-26T02:00:00Z"
    assert article["updated"] == "2026-10-26T02:30:00Z"
    assert article["confidence"] == 0.98
    assert article["stdp_engrams"] == 42
    assert article["status"] == "CANONICAL"
    assert article["category"] == "Architecture"
    assert "test" in article["tags"]
    assert "architecture" in article["tags"]
    assert "This is a test executive summary" in article["executive_summary"]
    assert "## Core Pillars" in article["body"]


def test_obsidian_wiki_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/wiki returns synthesized wiki articles."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/wiki")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["count"] >= 6
    titles = [a["title"] for a in data["articles"]]
    assert any("Vaelor" in t for t in titles)
    assert any("Biomorphic STDP" in t for t in titles)


def test_obsidian_audit_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/audit returns doctor audit metrics."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/audit")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["score"] == 100
    assert data["status"] in ("PERFECT", "HEALTHY")
    assert data["canvasesValid"] >= 14
    assert data["basesValid"] >= 18
    assert data["totalNotes"] >= 80
    assert data["connectivityPct"] > 90.0


def test_obsidian_status_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/status returns vault inventory."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/status")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert len(data["canvases"]) >= 14
    assert len(data["bases"]) >= 18
    assert len(data["wikiArticles"]) >= 10


def test_obsidian_wiki_post_validation(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/wiki requires topic."""
    _, base_url, _ = obsidian_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/wiki", {"topic": ""})
    assert exc_info.value.code == 400


def test_obsidian_wiki_post_synthesize(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/wiki synthesizes topic and ingests memory."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/wiki", {
        "topic": "Vaelor Account-Lattice & PoUW Protocol"
    })
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["status"] == "synthesized"
    assert "Vaelor" in data["article"]["title"]


def test_obsidian_sync_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/sync synchronizes vault artifacts into daemon memories."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/sync", {})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["status"] == "synced"
    assert len(data["canvases"]) >= 14
    assert len(data["bases"]) >= 18


def test_obsidian_canvases_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/canvases returns parsed JSON Canvas 1.0 topologies."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/canvases")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["count"] >= 14
    names = [c["name"] for c in data["canvases"]]
    assert any("Pillars" in n for n in names)
    assert any("Vaelor" in n for n in names)
    assert any("Marketplace" in n for n in names)


def test_obsidian_bases_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/bases returns parsed Obsidian Bases YAML databases."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["count"] >= 18
    names = [b["name"] for b in data["bases"]]
    assert any("Tools" in n for n in names)
    assert any("Fleet" in n for n in names)
    assert any("Wiki" in n for n in names)


def test_obsidian_canvas_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/canvas procedural JSON Canvas 1.0 synthesis."""
    _, base_url, _ = obsidian_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/canvas", {"topic": ""})
    assert exc_info.value.code == 400

    status, _, body = _http_post(f"{base_url}/api/obsidian/canvas", {"topic": "Wave11 Pytest Cluster"})
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    canvas = data["canvas"]
    assert canvas["nodeCount"] >= 3
    assert len(canvas["edges"]) >= 2


def test_obsidian_ingest_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/ingest creates Markdown note and stores STDP engram."""
    _, base_url, _ = obsidian_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/ingest", {"title": "", "content": ""})
    assert exc_info.value.code == 400

    status, _, body = _http_post(f"{base_url}/api/obsidian/ingest", {
        "title": "Wave 11 Pytest Ingestion Spec",
        "content": "Autonomous agents require zero-trust cryptographically verified boundaries.",
        "source": "pytest-unit-test",
        "tags": ["agents", "zero-trust", "pytest"]
    })
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    note = data["note"]
    assert note["title"] == "Wave 11 Pytest Ingestion Spec"
    ingested_file = Path.home() / "Documents" / "Obsidian Vault" / note["relPath"]
    assert ingested_file.exists()
    assert "[[00 Home]]" in ingested_file.read_text(encoding="utf-8")


def test_obsidian_search_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/search returns unified vault and STDP matches."""
    _, base_url, daemon = obsidian_server
    daemon.store(
        text="Vaelor PoUW consensus mechanism secures autonomous agent swarm payments.",
        tags=["vaelor", "pouw", "consensus"],
        importance=0.95,
        category="semantic"
    )

    status, _, body = _http_get(f"{base_url}/api/obsidian/search?q=")
    assert status == 200
    assert json.loads(body)["vaultCount"] == 0

    status, _, body = _http_get(f"{base_url}/api/obsidian/search?q=Vaelor")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["vaultCount"] > 0
    assert data["stdpCount"] > 0


def test_obsidian_search_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/search returns unified search results."""
    _, base_url, daemon = obsidian_server
    daemon.store(
        text="Hermes agent fleet synchronizes cognitive context across ZothOS nodes.",
        tags=["hermes", "fleet", "zothos"],
        importance=0.88,
        category="episodic"
    )
    status, _, body = _http_post(f"{base_url}/api/obsidian/search", {"query": "Hermes"})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["stdpCount"] > 0


def test_obsidian_telemetry_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/telemetry returns compiled telemetry markdown notes."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/telemetry")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["count"] >= 3
    titles = [n["title"] for n in data["notes"]]
    assert any("Neuro-Memory" in t for t in titles)
    assert any("Vaelor" in t for t in titles)


def test_obsidian_render_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/render invokes telemetry compilation."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/render", {"target": "all"})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["count"] >= 3


def test_obsidian_graph_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/graph returns vault degree centrality and top hubs."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/graph")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["totalNodes"] >= 80
    assert data["totalEdges"] >= 100
    assert len(data["topHubs"]) >= 10


def test_mcp_obsidian_vault_search(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 101, "method": "tools/call",
        "params": {"name": "obsidian_vault_search", "arguments": {"query": "Vaelor", "limit": 5}}
    })
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["vaultCount"] > 0


def test_mcp_obsidian_wiki_synthesize(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 102, "method": "tools/call",
        "params": {"name": "obsidian_wiki_synthesize", "arguments": {"topic": "Vaelor Account-Lattice & PoUW Protocol"}}
    })
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["status"] == "synthesized"


def test_mcp_obsidian_canvas_generate(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 103, "method": "tools/call",
        "params": {"name": "obsidian_canvas_generate", "arguments": {"topic": "Wave 16 MCP Test Canvas"}}
    })
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["canvas"]["nodeCount"] >= 3


def test_mcp_obsidian_doctor_audit(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 104, "method": "tools/call",
        "params": {"name": "obsidian_doctor_audit", "arguments": {}}
    })
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["score"] == 100
    assert content["totalCanvases"] >= 14
    assert content["totalBases"] >= 18


def test_api_mcp_tools_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/mcp/tools")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["count"] == 21
    assert len(data["tools"]) == 21


def test_api_mcp_call_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {"name": "obsidian_doctor_audit", "arguments": {}})
    assert status == 200
    assert json.loads(body)["result"]["score"] == 100

    status, _, body = _http_post(f"{base_url}/api/mcp/call", {"name": "memory_stats", "arguments": {}})
    assert status == 200

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/mcp/call", {"arguments": {}})
    assert exc_info.value.code == 400

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/mcp/call", {"name": "nonexistent_mcp_tool"})
    assert exc_info.value.code == 404


def test_obsidian_bases_records_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases/records?name=Zoth%2072%20Sovereign%20Tools.base")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["totalMatched"] >= 71

    status, _, body = _http_get(f"{base_url}/api/obsidian/bases/records?name=Zoth%20LLM%20Wiki%20Index.base")
    assert status == 200
    assert json.loads(body)["totalMatched"] >= 10


def test_obsidian_daily_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/daily")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "07-Daily" in data["relPath"]
    assert data["entriesCount"] >= 1


def test_obsidian_daily_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/daily", {"entry": "Automated pytest engineering log verification."})
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["entriesCount"] >= 2

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/daily", {"entry": "  "})
    assert exc_info.value.code == 400


def test_mcp_obsidian_daily_log(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 201, "method": "tools/call",
        "params": {"name": "obsidian_daily_log", "arguments": {"entry": "Synthesized Wave 20 Wiki articles."}}
    })
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert "Synthesized Wave 20" in content["content"]


def test_obsidian_bundle_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/bundle")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["healthScore"] == 100
    assert len(data["bundleSha256"]) == 64


def test_obsidian_backlinks_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/backlinks?note=00%20Home")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["outgoingCount"] >= 50
    assert data["backlinksCount"] >= 40

    status, _, body = _http_get(f"{base_url}/api/obsidian/backlinks?note=Zoth%20OS")
    assert status == 200
    os_data = json.loads(body.decode("utf-8"))
    assert os_data["ok"] is True
    assert os_data["backlinksCount"] >= 70
    assert os_data["unlinkedCount"] >= 5


def test_obsidian_backlinks_link_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    test_note = vault_dir / "04-Ingested" / "test-backlink-auto-link.md"
    test_note.write_text(
        "---\ntitle: \"Test\"\n---\n\n# Heading Zoth OS\n\nPlain Zoth OS mention.\n[[Zoth OS]]\n```bash\necho \"Zoth OS\"\n```\nAnother Zoth OS mention.\n",
        encoding="utf-8",
    )
    status, _, body = _http_post(f"{base_url}/api/obsidian/backlinks/link", {
        "sourcePath": "04-Ingested/test-backlink-auto-link.md",
        "targetTitle": "Zoth OS"
    })
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["linkedCount"] == 3
    assert 'echo "Zoth OS"' in test_note.read_text(encoding="utf-8")


def test_mcp_obsidian_backlinks_inspect(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 401, "method": "tools/call",
        "params": {"name": "obsidian_backlinks_inspect", "arguments": {"note": "00 Home"}}
    })
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["outgoingCount"] >= 50


def test_mcp_obsidian_bundle_export(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 501, "method": "tools/call",
        "params": {"name": "obsidian_bundle_export", "arguments": {"refresh": False}}
    })
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert len(content["bundleSha256"]) == 64


def test_obsidian_note_get_and_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/note")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["title"] == "00 Home"

    test_rel = "04-Ingested/test-wave25-note.md"
    status, _, body = _http_post(f"{base_url}/api/obsidian/note", {
        "relPath": test_rel,
        "content": "---\ntitle: \"Wave 25\"\n---\n\n> [!important] Callout\n> Link [[00 Home]].\n"
    })
    assert status == 200
    status, _, body = _http_get(f"{base_url}/api/obsidian/note?path={urllib.parse.quote(test_rel)}")
    assert status == 200
    assert "00 Home" in json.loads(body)["wikilinks"]


def test_obsidian_note_path_traversal_rejected(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, _ = obsidian_server
    for bad_path in ("../../etc/passwd", "/etc/passwd", "../shadow", "04-Ingested/../../../../etc/hosts"):
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _http_get(f"{base_url}/api/obsidian/note?path={urllib.parse.quote(bad_path)}")
        assert exc_info.value.code == 400
        with pytest.raises(urllib.error.HTTPError) as exc_info_post:
            _http_post(f"{base_url}/api/obsidian/note", {"relPath": bad_path, "content": "Malicious"})
        assert exc_info_post.value.code == 400


def test_mcp_obsidian_note_read_and_write(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 601, "method": "tools/call",
        "params": {"name": "obsidian_note_read", "arguments": {"path": "00 Home.md"}}
    })
    assert json.loads(resp["result"]["content"][0]["text"])["ok"] is True

    test_rel = "04-Ingested/mcp-test-note.md"
    resp_w = mcp.handle_request({
        "jsonrpc": "2.0", "id": 602, "method": "tools/call",
        "params": {"name": "obsidian_note_write", "arguments": {"relPath": test_rel, "content": "# Test\n[[00 Home]]"}}
    })
    assert json.loads(resp_w["result"]["content"][0]["text"])["ok"] is True


def test_mcp_obsidian_note_path_traversal_rejected(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    for bad_path in ("../../etc/passwd", "/etc/passwd", "../shadow"):
        resp = mcp.handle_request({
            "jsonrpc": "2.0", "id": 603, "method": "tools/call",
            "params": {"name": "obsidian_note_read", "arguments": {"path": bad_path}}
        })
        assert json.loads(resp["result"]["content"][0]["text"])["ok"] is False


def test_obsidian_vaelor_get(obsidian_server):
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/vaelor")
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert data["ok"] is True
    assert data["chainId"] == "vaelor-mainnet-1"
    assert data["validatorCount"] == 5


def test_obsidian_vaelor_mine_post(obsidian_server):
    _, base_url, daemon = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/vaelor/mine", {
        "miner": "@zoth",
        "taskType": "STDP_OBSIDIAN_INDEXING"
    })
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert data["ok"] is True
    assert data["quorumStatus"] == "FINALIZED_BFT"
    assert any("vaelor" in [t.lower() for t in m.tags] for m in daemon.nodes.values())


def test_mcp_obsidian_vaelor_pouw(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    resp = mcp.handle_request({
        "jsonrpc": "2.0", "id": 201, "method": "tools/call",
        "params": {"name": "obsidian_vaelor_pouw", "arguments": {"action": "status"}}
    })
    assert json.loads(resp["result"]["content"][0]["text"])["ok"] is True

    status, _, body = _http_post(f"{base_url}/api/mcp", {
        "jsonrpc": "2.0", "id": 303, "method": "tools/call",
        "params": {"name": "obsidian_vaelor_pouw", "arguments": {"action": "status"}}
    })
    assert status == 200
    assert json.loads(body)["jsonrpc"] == "2.0"
