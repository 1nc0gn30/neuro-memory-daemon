"""Tests for Obsidian Second Brain Wiki, Audit, and Sync REST API endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Generator

import pytest

from neuro_memory_daemon import MemoryDaemon
from neuro_memory_daemon.mcp_server import MCPServer
from neuro_memory_daemon.ui_server import MemoryUIServer, start_server_in_thread, _parse_wiki_article
from tests.test_ui_server import get_free_port, _http_get, _http_post


@pytest.fixture
def obsidian_server(temp_dir: Path) -> Generator[tuple[MemoryUIServer, str, MemoryDaemon], None, None]:
    """Start an ephemeral test server for Obsidian API testing."""
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    if not (vault_dir / "00 Home.md").exists():
        pytest.skip("Local Obsidian Vault not populated on CI runner")
    port = get_free_port()
    db_file = temp_dir / "obsidian_test_db.json"
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


def test_parse_wiki_article_unit(temp_dir: Path):
    """Test unit parsing of Obsidian Flavored Markdown with YAML frontmatter & callout."""
    wiki_file = temp_dir / "Test Article.md"
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
    assert "count" in data
    assert data["count"] >= 6
    assert "articles" in data
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
    assert data["canvasesValid"] >= 6
    assert data["basesValid"] >= 5
    assert data["totalNotes"] >= 1000
    assert data["connectivityPct"] > 90.0


def test_obsidian_status_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/status returns vault inventory."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/status")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "vaultPath" in data
    assert "canvases" in data
    assert "bases" in data
    assert "wikiArticles" in data
    assert len(data["canvases"]) >= 6
    assert len(data["bases"]) >= 5
    assert len(data["wikiArticles"]) >= 6


def test_obsidian_wiki_post_validation(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/wiki requires topic."""
    _, base_url, _ = obsidian_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/wiki", {"topic": ""})
    assert exc_info.value.code == 400


def test_obsidian_wiki_post_synthesize(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/wiki synthesizes topic and ingests memory."""
    _, base_url, daemon = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/wiki", {
        "topic": "Vaelor Account-Lattice & PoUW Protocol"
    })
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["status"] == "synthesized"
    assert "article" in data
    assert "Vaelor" in data["article"]["title"]


def test_obsidian_sync_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/sync synchronizes vault artifacts into daemon memories."""
    _, base_url, daemon = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/sync", {})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["status"] == "synced"
    assert "canvases" in data
    assert "bases" in data
    assert "wikiArticles" in data
    assert len(data["canvases"]) >= 6
    assert len(data["bases"]) >= 5


def test_obsidian_canvases_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/canvases returns parsed JSON Canvas 1.0 topologies."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/canvases")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "count" in data
    assert data["count"] >= 14
    assert "canvases" in data
    canvases = data["canvases"]
    names = [c["name"] for c in canvases]
    assert any("Pillars" in n for n in names)
    assert any("Vaelor" in n for n in names)
    assert any("Marketplace" in n for n in names)
    for c in canvases:
        assert "name" in c
        assert "relPath" in c
        assert "nodeCount" in c
        assert "edgeCount" in c
        assert "groupCount" in c
        assert "nodes" in c
        assert "edges" in c


def test_obsidian_bases_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/bases returns parsed Obsidian Bases YAML databases."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "count" in data
    assert data["count"] >= 18
    assert "bases" in data
    bases = data["bases"]
    names = [b["name"] for b in bases]
    assert any("Tools" in n for n in names)
    assert any("Fleet" in n for n in names)
    assert any("Wiki" in n for n in names)
    for b in bases:
        assert "name" in b
        assert "relPath" in b
        assert "viewCount" in b
        assert "views" in b
        assert "formulas" in b
        assert "properties" in b
        assert "rawYaml" in b


def test_obsidian_canvas_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/canvas procedural JSON Canvas 1.0 synthesis."""
    _, base_url, _ = obsidian_server

    # Validation check: empty topic returns 400
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/canvas", {"topic": ""})
    assert exc_info.value.code == 400

    # Successful canvas generation
    test_topic = "Wave11 Pytest Cluster"
    status, _, body = _http_post(f"{base_url}/api/obsidian/canvas", {"topic": test_topic})
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "canvas" in data
    canvas = data["canvas"]
    assert "name" in canvas
    assert "relPath" in canvas
    assert canvas["nodeCount"] >= 1
    assert "nodes" in canvas
    assert "edges" in canvas

    # Cleanup generated canvas file
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    gen_file = vault_dir / canvas["name"]
    if gen_file.exists():
        try:
            gen_file.unlink()
        except Exception:
            pass


def test_obsidian_ingest_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/ingest creates Markdown note and stores STDP engram."""
    _, base_url, daemon = obsidian_server

    # Validation check: missing title/content returns 400
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/ingest", {"title": "", "content": ""})
    assert exc_info.value.code == 400

    # Successful ingestion
    test_payload = {
        "title": "Wave 11 Pytest Ingestion Spec",
        "content": "Autonomous agents require zero-trust cryptographically verified supply chain boundaries.",
        "source": "pytest-unit-test",
        "tags": ["agents", "zero-trust", "pytest"]
    }
    status, _, body = _http_post(f"{base_url}/api/obsidian/ingest", test_payload)
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "note" in data
    note = data["note"]
    assert note["title"] == "Wave 11 Pytest Ingestion Spec"
    assert "slug" in note
    assert "relPath" in note
    assert "memoryId" in note

    # Verify physical file was written with YAML frontmatter
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    ingested_file = vault_dir / note["relPath"]
    assert ingested_file.exists()
    content_text = ingested_file.read_text(encoding="utf-8")
    assert "---" in content_text
    assert "title: \"Wave 11 Pytest Ingestion Spec\"" in content_text
    assert "[[00 Home]]" in content_text

    # Cleanup test file
    try:
        ingested_file.unlink()
    except Exception:
        pass


def test_obsidian_search_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/search returns unified vault and STDP matches."""
    _, base_url, daemon = obsidian_server

    # Seed an STDP engram into the test daemon
    daemon.store(
        text="Vaelor PoUW consensus mechanism secures autonomous agent swarm payments.",
        tags=["vaelor", "pouw", "consensus"],
        importance=0.95,
        category="semantic"
    )

    # Empty search query
    status, _, body = _http_get(f"{base_url}/api/obsidian/search?q=")
    assert status == 200
    empty_data = json.loads(body.decode("utf-8"))
    assert empty_data["ok"] is True
    assert empty_data["vaultCount"] == 0
    assert empty_data["stdpCount"] == 0

    # Search for "Vaelor"
    status, _, body = _http_get(f"{base_url}/api/obsidian/search?q=Vaelor")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["query"] == "Vaelor"
    assert data["vaultCount"] > 0
    assert "vaultMatches" in data
    assert "stdpMatches" in data
    assert data["stdpCount"] > 0

    first_vm = data["vaultMatches"][0]
    assert "title" in first_vm
    assert "relPath" in first_vm
    assert "type" in first_vm
    assert "snippet" in first_vm
    assert "wikilinks" in first_vm

    first_sm = data["stdpMatches"][0]
    assert "id" in first_sm
    assert "content" in first_sm
    assert "importance" in first_sm
    assert "category" in first_sm
    assert "tags" in first_sm
    assert "Vaelor" in first_sm["content"] or "vaelor" in [t.lower() for t in first_sm["tags"]]


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
    assert data["query"] == "Hermes"
    assert "vaultMatches" in data
    assert "stdpMatches" in data
    assert data["stdpCount"] > 0
    assert any("Hermes" in sm["content"] for sm in data["stdpMatches"])


def test_obsidian_telemetry_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/telemetry returns compiled telemetry markdown notes."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/telemetry")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "count" in data
    assert "notes" in data
    assert data["count"] >= 3
    titles = [n["title"] for n in data["notes"]]
    assert any("Neuro-Memory" in t for t in titles)
    assert any("Vaelor" in t for t in titles)
    first_note = data["notes"][0]
    assert "relPath" in first_note
    assert "updated" in first_note
    assert "content" in first_note
    assert "---" in first_note["content"]


def test_obsidian_render_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/render invokes Knap telemetry compilation."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/render", {"target": "all"})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["target"] == "all"
    assert "notes" in data
    assert data["count"] >= 3
    titles = [n["title"] for n in data["notes"]]
    assert any("Neuro-Memory" in t for t in titles)


def test_obsidian_graph_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/graph returns vault degree centrality and top hubs."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/graph")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "totalNodes" in data
    assert "totalEdges" in data
    assert "clusters" in data
    assert "topHubs" in data
    assert data["totalNodes"] >= 1600
    assert data["totalEdges"] >= 5000
    assert len(data["topHubs"]) >= 10
    first_hub = data["topHubs"][0]
    assert "title" in first_hub
    assert "relPath" in first_hub
    assert "inDegree" in first_hub
    assert "outDegree" in first_hub
    assert "totalDegree" in first_hub
    assert "cluster" in first_hub
    assert first_hub["totalDegree"] >= first_hub["inDegree"]


def test_mcp_obsidian_vault_search(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_vault_search via JSON-RPC."""
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_vault_search" in mcp.tools

    req = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {
            "name": "obsidian_vault_search",
            "arguments": {"query": "Vaelor", "limit": 5}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["query"] == "Vaelor"
    assert content["vaultCount"] > 0
    assert "vaultMatches" in content


def test_mcp_obsidian_wiki_synthesize(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_wiki_synthesize via JSON-RPC."""
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_wiki_synthesize" in mcp.tools

    req = {
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/call",
        "params": {
            "name": "obsidian_wiki_synthesize",
            "arguments": {"topic": "Vaelor Account-Lattice & PoUW Protocol"}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["status"] == "synthesized"
    assert "Vaelor" in content["article"]["title"]


def test_mcp_obsidian_canvas_generate(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_canvas_generate via JSON-RPC."""
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_canvas_generate" in mcp.tools

    req = {
        "jsonrpc": "2.0",
        "id": 103,
        "method": "tools/call",
        "params": {
            "name": "obsidian_canvas_generate",
            "arguments": {"topic": "Wave 16 MCP Test Canvas"}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert "canvas" in content
    canvas = content["canvas"]
    assert canvas["nodeCount"] >= 3
    assert canvas["edgeCount"] >= 2

    # Cleanup generated canvas file
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    canvas_file = vault_dir / canvas["name"]
    try:
        if canvas_file.exists():
            canvas_file.unlink()
    except Exception:
        pass


def test_mcp_obsidian_doctor_audit(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_doctor_audit via JSON-RPC."""
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_doctor_audit" in mcp.tools

    req = {
        "jsonrpc": "2.0",
        "id": 104,
        "method": "tools/call",
        "params": {
            "name": "obsidian_doctor_audit",
            "arguments": {}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["score"] == 100
    assert content["healthGrade"] == "✦ PERFECT"
    assert content["totalCanvases"] >= 14
    assert content["totalBases"] >= 18
    assert "topHubs" in content


def test_api_mcp_tools_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/mcp/tools returns list of 21 registered tools."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/mcp/tools")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["count"] == 21
    assert len(data["tools"]) == 21
    tool_names = [t["name"] for t in data["tools"]]
    assert "obsidian_doctor_audit" in tool_names
    assert "obsidian_vault_search" in tool_names
    assert "obsidian_wiki_synthesize" in tool_names
    assert "obsidian_canvas_generate" in tool_names
    assert "obsidian_daily_log" in tool_names
    assert "obsidian_backlinks_inspect" in tool_names
    assert "obsidian_bundle_export" in tool_names
    assert "obsidian_note_read" in tool_names
    assert "obsidian_note_write" in tool_names
    assert "obsidian_vaelor_pouw" in tool_names
    assert "memory_store" in tool_names
    assert "memory_recall" in tool_names


def test_api_mcp_call_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/mcp/call invokes registered MCP tools and handles errors."""
    _, base_url, _ = obsidian_server

    # 1. Successful execution of obsidian_doctor_audit
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "obsidian_doctor_audit",
        "arguments": {}
    })
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["tool"] == "obsidian_doctor_audit"
    assert "result" in data
    assert data["result"]["ok"] is True
    assert data["result"]["score"] == 100
    assert data["result"]["healthGrade"] == "✦ PERFECT"

    # 2. Execution of memory_stats
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "memory_stats",
        "arguments": {}
    })
    assert status == 200
    stats_data = json.loads(body.decode("utf-8"))
    assert stats_data["ok"] is True
    assert stats_data["tool"] == "memory_stats"

    # 3. Validation error: missing 'name' returns 400
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/mcp/call", {"arguments": {}})
    assert exc_info.value.code == 400

    # 4. Unknown tool returns 404
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/mcp/call", {"name": "nonexistent_mcp_tool"})
    assert exc_info.value.code == 404


def test_obsidian_bases_records_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/bases/records returns parsed base records."""
    _, base_url, _ = obsidian_server

    # 1. Query Zoth 72/71 Sovereign Tools.base
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases/records?name=Zoth%2071%20Sovereign%20Tools.base")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["baseName"] in ("Zoth 72 Sovereign Tools.base", "Zoth 71 Sovereign Tools.base")
    assert data["totalMatched"] >= 71
    assert len(data["columns"]) >= 5
    assert len(data["rows"]) >= 71
    first_row = data["rows"][0]
    assert "title" in first_row
    assert "relPath" in first_row
    assert "properties" in first_row
    props = first_row["properties"]
    assert "file.name" in props
    assert "pillar" in props or "category" in props
    assert "formula.status_badge" in props

    # 2. Query Zoth LLM Wiki Index.base
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases/records?name=Zoth%20LLM%20Wiki%20Index.base")
    assert status == 200
    wiki_data = json.loads(body.decode("utf-8"))
    assert wiki_data["ok"] is True
    assert wiki_data["totalMatched"] >= 10
    assert len(wiki_data["rows"]) >= 10

    # 3. Query without name defaults to tools
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases/records")
    assert status == 200
    default_data = json.loads(body.decode("utf-8"))
    assert default_data["ok"] is True
    assert default_data["totalMatched"] >= 71


def test_obsidian_daily_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/daily returns today's Daily Sovereign Note."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/daily")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "date" in data
    assert "relPath" in data
    assert "07-Daily" in data["relPath"]
    assert "content" in data
    assert "Daily Sovereign Note" in data["content"]
    assert "Live Sovereign Snapshot" in data["content"]
    assert "entriesCount" in data
    assert data["entriesCount"] >= 1


def test_obsidian_daily_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/daily appends an engineering log entry and STDP engram."""
    _, base_url, daemon = obsidian_server

    # 1. Successful append
    status, _, body = _http_post(f"{base_url}/api/obsidian/daily", {
        "entry": "Automated pytest engineering log verification."
    })
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "Automated pytest engineering log verification." in data["content"]
    assert "appended" in data
    assert "Automated pytest engineering log verification." in data["appended"]
    assert data["entriesCount"] >= 2

    # 2. Validation error: missing entry returns 400
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/daily", {"entry": "  "})
    assert exc_info.value.code == 400


def test_mcp_obsidian_daily_log(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test obsidian_daily_log MCP tool via direct JSON-RPC and HTTP API."""
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_daily_log" in mcp.tools

    # 1. Direct MCP JSON-RPC call without entry (retrieval)
    req = {
        "jsonrpc": "2.0",
        "id": 201,
        "method": "tools/call",
        "params": {
            "name": "obsidian_daily_log",
            "arguments": {}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert "date" in content
    assert "relPath" in content
    assert "07-Daily" in content["relPath"]
    assert "Daily Sovereign Note" in content["content"]
    assert "Live Sovereign Snapshot" in content["content"]
    assert content["entriesCount"] >= 1

    # 2. Direct MCP JSON-RPC call with entry (append + STDP memory store)
    req2 = {
        "jsonrpc": "2.0",
        "id": 202,
        "method": "tools/call",
        "params": {
            "name": "obsidian_daily_log",
            "arguments": {
                "entry": "Synthesized Wave 20 Karpathy LLM Wiki articles & registered 16th MCP tool."
            }
        }
    }
    resp2 = mcp.handle_request(req2)
    assert resp2 is not None
    assert not resp2["result"].get("isError", False)
    content2 = json.loads(resp2["result"]["content"][0]["text"])
    assert content2["ok"] is True
    assert "Synthesized Wave 20 Karpathy LLM Wiki articles" in content2["content"]
    assert content2["entriesCount"] >= 2

    # Verify episodic STDP memory was recorded
    mem_matches = [
        m for m in daemon.nodes.values()
        if "Synthesized Wave 20 Karpathy LLM Wiki articles" in getattr(m, "text", "")
    ]
    assert len(mem_matches) >= 1
    assert "daily-note" in mem_matches[0].tags

    # 3. HTTP POST /api/mcp/call invocation
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "obsidian_daily_log",
        "arguments": {
            "entry": "HTTP MCP tool invocation verification."
        }
    })
    assert status == 200
    http_data = json.loads(body.decode("utf-8"))
    assert http_data["ok"] is True
    assert http_data["tool"] == "obsidian_daily_log"
    assert "HTTP MCP tool invocation verification." in http_data["result"]["content"]


def test_obsidian_bundle_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/bundle returns SHA-256 verified knowledge bundle."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/bundle")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["version"] == "1.0.0"
    assert data["healthScore"] == 100
    assert "bundleSha256" in data
    assert len(data["bundleSha256"]) == 64
    assert "auditMetrics" in data
    metrics = data["auditMetrics"]
    assert metrics["totalNotes"] >= 1720
    assert metrics["canvasesCount"] >= 14
    assert metrics["basesCount"] >= 18
    assert metrics["wikiCount"] >= 10
    assert "wikiArticles" in data
    assert len(data["wikiArticles"]) >= 10
    assert "canvases" in data
    assert len(data["canvases"]) >= 14
    assert "bases" in data
    assert len(data["bases"]) >= 18
    assert "topHubs" in data
    assert "dailyNote" in data


def test_obsidian_backlinks_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/backlinks returns incoming backlinks, outlinks & unlinked mentions."""
    _, base_url, _ = obsidian_server

    # 1. Inspect 00 Home
    status, _, body = _http_get(f"{base_url}/api/obsidian/backlinks?note=00%20Home")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["note"]["title"] == "00 Home"
    assert "00 Home.md" in data["note"]["relPath"]
    assert data["note"]["cluster"] == "Root"
    assert data["note"]["wordCount"] > 100
    assert data["outgoingCount"] >= 50
    assert len(data["outgoingLinks"]) >= 50
    assert data["backlinksCount"] >= 40
    assert len(data["incomingBacklinks"]) >= 40
    assert "unlinkedCount" in data

    # 2. Inspect Zoth OS (high centrality hub with unlinked mentions)
    status, _, body = _http_get(f"{base_url}/api/obsidian/backlinks?note=Zoth%20OS")
    assert status == 200
    os_data = json.loads(body.decode("utf-8"))
    assert os_data["ok"] is True
    assert os_data["note"]["title"] == "Zoth OS"
    assert os_data["backlinksCount"] >= 1000
    assert os_data["unlinkedCount"] >= 5
    assert len(os_data["unlinkedMentions"]) >= 5
    first_unlinked = os_data["unlinkedMentions"][0]
    assert "sourceTitle" in first_unlinked
    assert "snippet" in first_unlinked

    # 3. Default without note param defaults to 00 Home
    status, _, body = _http_get(f"{base_url}/api/obsidian/backlinks")
    assert status == 200
    def_data = json.loads(body.decode("utf-8"))
    assert def_data["ok"] is True
    assert def_data["note"]["title"] == "00 Home"

    # 4. Non-existent note returns ok: false with error
    status, _, body = _http_get(f"{base_url}/api/obsidian/backlinks?note=TotallyNonExistentNote12345")
    assert status == 200
    err_data = json.loads(body.decode("utf-8"))
    assert err_data["ok"] is False
    assert "not found" in err_data["error"]


def test_obsidian_backlinks_link_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/backlinks/link safely auto-links plaintext mentions."""
    _, base_url, _ = obsidian_server
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    test_note = vault_dir / "04-Ingested" / "test-backlink-auto-link.md"

    initial_content = """---
title: "Test Backlink Auto Link"
tags: [test, auto-link]
---

# Test Heading with Zoth OS

Here is a plaintext Zoth OS mention in a paragraph.
Here is an existing [[Zoth OS]] wikilink.
```bash
echo "Zoth OS"
```
And another plaintext Zoth OS mention at the end.
"""
    try:
        test_note.parent.mkdir(parents=True, exist_ok=True)
        test_note.write_text(initial_content, encoding="utf-8")

        # 1. Successful auto-link conversion
        status, _, body = _http_post(f"{base_url}/api/obsidian/backlinks/link", {
            "sourcePath": "04-Ingested/test-backlink-auto-link.md",
            "targetTitle": "Zoth OS"
        })
        assert status == 200
        data = json.loads(body.decode("utf-8"))
        assert data["ok"] is True
        assert data["sourcePath"] == "04-Ingested/test-backlink-auto-link.md"
        assert data["targetTitle"] == "Zoth OS"
        assert data["linkedCount"] == 3

        # Verify file content
        updated_txt = test_note.read_text(encoding="utf-8")
        assert 'echo "Zoth OS"' in updated_txt  # code block preserved
        assert "title: \"Test Backlink Auto Link\"" in updated_txt  # frontmatter preserved
        assert "[[Zoth OS]]" in updated_txt
        assert "[[[[" not in updated_txt

        # 2. Validation error: missing fields
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _http_post(f"{base_url}/api/obsidian/backlinks/link", {
                "sourcePath": "04-Ingested/test-backlink-auto-link.md"
            })
        assert exc_info.value.code == 400

        # 3. Non-existent file error
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _http_post(f"{base_url}/api/obsidian/backlinks/link", {
                "sourcePath": "04-Ingested/non-existent-note-xyz.md",
                "targetTitle": "Zoth OS"
            })
        assert exc_info.value.code == 404
    finally:
        if test_note.exists():
            test_note.unlink()


def test_mcp_obsidian_backlinks_inspect(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test obsidian_backlinks_inspect MCP tool via direct JSON-RPC and HTTP API."""
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_backlinks_inspect" in mcp.tools

    # 1. Direct MCP JSON-RPC call
    req = {
        "jsonrpc": "2.0",
        "id": 401,
        "method": "tools/call",
        "params": {
            "name": "obsidian_backlinks_inspect",
            "arguments": {
                "note": "00 Home"
            }
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["note"]["title"] == "00 Home"
    assert content["outgoingCount"] >= 50
    assert content["backlinksCount"] >= 40

    # 2. HTTP POST /api/mcp/call invocation
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "obsidian_backlinks_inspect",
        "arguments": {
            "note": "Zoth OS"
        }
    })
    assert status == 200
    http_data = json.loads(body.decode("utf-8"))
    assert http_data["ok"] is True
    assert http_data["tool"] == "obsidian_backlinks_inspect"
    assert http_data["result"]["note"]["title"] == "Zoth OS"
    assert http_data["result"]["backlinksCount"] >= 1000


def test_mcp_obsidian_bundle_export(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test obsidian_bundle_export MCP tool via JSON-RPC and HTTP API."""
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_bundle_export" in mcp.tools

    # 1. Direct MCP JSON-RPC call
    req = {
        "jsonrpc": "2.0",
        "id": 501,
        "method": "tools/call",
        "params": {
            "name": "obsidian_bundle_export",
            "arguments": {
                "refresh": False
            }
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["healthScore"] == 100
    assert content["version"] == "1.0.0"
    assert len(content["bundleSha256"]) == 64
    assert content["wikiCount"] >= 6
    assert content["canvasesCount"] >= 14
    assert content["basesCount"] >= 18
    assert len(content["topHubs"]) >= 5

    # 2. HTTP POST /api/mcp/call invocation
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "obsidian_bundle_export",
        "arguments": {}
    })
    assert status == 200
    http_data = json.loads(body.decode("utf-8"))
    assert http_data["ok"] is True
    assert http_data["tool"] == "obsidian_bundle_export"
    assert http_data["result"]["ok"] is True
    assert http_data["result"]["healthScore"] == 100
    assert len(http_data["result"]["bundleSha256"]) == 64
    assert "auditMetrics" in http_data["result"]


def test_obsidian_note_get_and_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/note and POST /api/obsidian/note endpoints."""
    _, base_url, _ = obsidian_server

    # 1. GET default 00 Home.md
    status, _, body = _http_get(f"{base_url}/api/obsidian/note")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["title"] == "00 Home"
    assert data["relPath"] == "00 Home.md"
    assert data["wordCount"] > 100
    assert "content" in data
    assert isinstance(data["wikilinks"], list)
    assert len(data["wikilinks"]) >= 50

    # 2. GET note by title
    status, _, body = _http_get(f"{base_url}/api/obsidian/note?path=Zoth%20OS")
    assert status == 200
    zdata = json.loads(body.decode("utf-8"))
    assert zdata["ok"] is True
    assert zdata["title"] == "Zoth OS"
    assert "frontmatter" in zdata

    # 3. POST new temporary note
    test_rel = "04-Ingested/test-wave25-note.md"
    note_content = """---
title: "Wave 25 Test Note"
tags: [ofm, wave25, test]
---

# Wave 25 Test Note

> [!important] Architecture Callout
> This note tests live OFM reading and saving.

Here is a link to [[00 Home]] and [[Zoth OS]].
"""
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    test_file = vault_dir / test_rel
    try:
        status, _, body = _http_post(f"{base_url}/api/obsidian/note", {
            "relPath": test_rel,
            "content": note_content
        })
        assert status == 200
        post_data = json.loads(body.decode("utf-8"))
        assert post_data["ok"] is True
        assert post_data["relPath"] == test_rel
        assert post_data["wordCount"] > 10
        assert "updatedAt" in post_data

        # 4. GET the saved note
        status, _, body = _http_get(f"{base_url}/api/obsidian/note?path={urllib.parse.quote(test_rel)}")
        assert status == 200
        read_back = json.loads(body.decode("utf-8"))
        assert read_back["ok"] is True
        assert read_back["title"] == "test-wave25-note"
        assert "00 Home" in read_back["wikilinks"]
        assert "important" in read_back["callouts"]
        assert read_back["frontmatter"].get("title") == "Wave 25 Test Note"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_obsidian_note_path_traversal_rejected(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test that path traversal attempts outside vault root are rejected with HTTP 400."""
    _, base_url, _ = obsidian_server

    traversal_paths = [
        "../../etc/passwd",
        "/etc/passwd",
        "../shadow",
        "04-Ingested/../../../../etc/hosts"
    ]

    for bad_path in traversal_paths:
        # GET check
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _http_get(f"{base_url}/api/obsidian/note?path={urllib.parse.quote(bad_path)}")
        assert exc_info.value.code == 400

        # POST check
        with pytest.raises(urllib.error.HTTPError) as exc_info_post:
            _http_post(f"{base_url}/api/obsidian/note", {
                "relPath": bad_path,
                "content": "Malicious payload attempt"
            })
        assert exc_info_post.value.code == 400


def test_mcp_obsidian_note_read_and_write(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tools obsidian_note_read and obsidian_note_write via JSON-RPC and HTTP API."""
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_note_read" in mcp.tools
    assert "obsidian_note_write" in mcp.tools

    # 1. Read existing note via JSON-RPC
    req_read = {
        "jsonrpc": "2.0",
        "id": 601,
        "method": "tools/call",
        "params": {
            "name": "obsidian_note_read",
            "arguments": {"path": "00 Home.md"}
        }
    }
    resp_read = mcp.handle_request(req_read)
    assert resp_read is not None
    assert not resp_read["result"].get("isError", False)
    content_read = json.loads(resp_read["result"]["content"][0]["text"])
    assert content_read["ok"] is True
    assert content_read["title"] == "00 Home"
    assert content_read["wordCount"] > 100
    assert len(content_read["wikilinks"]) >= 50

    # 2. Write note via JSON-RPC
    test_rel = "04-Ingested/mcp-test-wave26-note.md"
    test_content = """---
title: "MCP Wave 26 Test Note"
tags: [mcp, wave26, test]
---

# MCP Wave 26 Test Note

> [!tip] MCP 20-Tool Suite
> Testing obsidian_note_write tool.

Linked to [[00 Home]] and [[Zoth Memory]].
"""
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    test_file = vault_dir / test_rel
    try:
        req_write = {
            "jsonrpc": "2.0",
            "id": 602,
            "method": "tools/call",
            "params": {
                "name": "obsidian_note_write",
                "arguments": {
                    "relPath": test_rel,
                    "content": test_content
                }
            }
        }
        resp_write = mcp.handle_request(req_write)
        assert resp_write is not None
        assert not resp_write["result"].get("isError", False)
        content_write = json.loads(resp_write["result"]["content"][0]["text"])
        assert content_write["ok"] is True
        assert content_write["relPath"] == test_rel
        assert content_write["wordCount"] > 10

        # 3. Read back via HTTP POST /api/mcp/call
        status, _, body = _http_post(f"{base_url}/api/mcp/call", {
            "name": "obsidian_note_read",
            "arguments": {"path": test_rel}
        })
        assert status == 200
        http_data = json.loads(body.decode("utf-8"))
        assert http_data["ok"] is True
        assert http_data["result"]["ok"] is True
        assert http_data["result"]["title"] == "mcp-test-wave26-note"
        assert "00 Home" in http_data["result"]["wikilinks"]
        assert http_data["result"]["frontmatter"].get("title") == "MCP Wave 26 Test Note"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_mcp_obsidian_note_path_traversal_rejected(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test that path traversal attempts in MCP note tools are rejected."""
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)

    traversal_paths = [
        "../../etc/passwd",
        "/etc/passwd",
        "../shadow"
    ]

    for bad_path in traversal_paths:
        # 1. MCP Read
        req_read = {
            "jsonrpc": "2.0",
            "id": 603,
            "method": "tools/call",
            "params": {
                "name": "obsidian_note_read",
                "arguments": {"path": bad_path}
            }
        }
        resp_read = mcp.handle_request(req_read)
        assert resp_read is not None
        content_read = json.loads(resp_read["result"]["content"][0]["text"])
        assert content_read["ok"] is False
        assert "forbidden" in content_read["error"].lower()

        # 2. MCP Write
        req_write = {
            "jsonrpc": "2.0",
            "id": 604,
            "method": "tools/call",
            "params": {
                "name": "obsidian_note_write",
                "arguments": {
                    "relPath": bad_path,
                    "content": "Malicious content attempt"
                }
            }
        }
        resp_write = mcp.handle_request(req_write)
        assert resp_write is not None
        content_write = json.loads(resp_write["result"]["content"][0]["text"])
        assert content_write["ok"] is False
        assert "forbidden" in content_write["error"].lower()


def test_obsidian_vaelor_get(obsidian_server):
    """Test GET /api/obsidian/vaelor returns Vaelor network status with L1 metrics."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/vaelor")
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert data["ok"] is True
    assert data["chainId"] == "vaelor-mainnet-1"
    assert data["validatorCount"] == 5
    assert data["stakingApyPct"] == 8.5
    assert data["cashbackPct"] == 2.5
    assert data["gasFee"] == 0
    assert "totalSupplyVlr" in data
    assert "totalBlocks" in data


def test_obsidian_vaelor_mine_post(obsidian_server):
    """Test POST /api/obsidian/vaelor/mine executes PoUW cognitive mining and stores STDP engram."""
    _, base_url, daemon = obsidian_server
    payload = {
        "miner": "@zoth",
        "taskType": "STDP_OBSIDIAN_INDEXING"
    }
    status, _, body = _http_post(f"{base_url}/api/obsidian/vaelor/mine", payload)
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert data["ok"] is True
    assert data["miner"] == "@zoth"
    assert data["taskType"] == "STDP_OBSIDIAN_INDEXING"
    assert "rewardVlr" in data
    assert data["rewardVlr"] > 0
    assert "blockHash" in data
    assert len(data["blockHash"]) > 10
    assert data["quorumStatus"] == "FINALIZED_BFT"
    assert data["validatorCount"] == 5

    # Verify that an STDP memory engram was recorded in daemon
    vaelor_mems = [m for m in daemon.nodes.values() if "vaelor" in [t.lower() for t in m.tags]]
    assert len(vaelor_mems) >= 1
    assert any("pouw" in [t.lower() for t in m.tags] for m in vaelor_mems)


def test_mcp_obsidian_vaelor_pouw(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_vaelor_pouw via JSON-RPC, HTTP /api/mcp/call, and HTTP /api/mcp."""
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_vaelor_pouw" in mcp.tools

    # 1. Test status action via MCPServer JSON-RPC
    req_status = {
        "jsonrpc": "2.0",
        "id": 201,
        "method": "tools/call",
        "params": {
            "name": "obsidian_vaelor_pouw",
            "arguments": {"action": "status"}
        }
    }
    resp_status = mcp.handle_request(req_status)
    assert resp_status is not None
    assert not resp_status["result"].get("isError", False)
    content_status = json.loads(resp_status["result"]["content"][0]["text"])
    assert content_status["ok"] is True
    assert content_status["action"] == "status"
    assert content_status["chainId"] == "vaelor-mainnet-1"
    assert content_status["validatorCount"] == 5
    assert content_status["stakingApyPct"] == 8.5
    assert "totalSupplyVlr" in content_status

    # 2. Test mine action via MCPServer JSON-RPC
    req_mine = {
        "jsonrpc": "2.0",
        "id": 202,
        "method": "tools/call",
        "params": {
            "name": "obsidian_vaelor_pouw",
            "arguments": {
                "action": "mine",
                "miner": "@zoth_mcp_tester",
                "task_type": "STDP_OBSIDIAN_INDEXING"
            }
        }
    }
    resp_mine = mcp.handle_request(req_mine)
    assert resp_mine is not None
    assert not resp_mine["result"].get("isError", False)
    content_mine = json.loads(resp_mine["result"]["content"][0]["text"])
    assert content_mine["ok"] is True
    assert content_mine["action"] == "mine"
    assert content_mine["miner"] == "@zoth_mcp_tester"
    assert content_mine["rewardVlr"] > 0
    assert "blockHash" in content_mine
    assert content_mine["quorumStatus"] == "FINALIZED_BFT"

    # 3. Test HTTP POST /api/mcp/call with obsidian_vaelor_pouw
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "obsidian_vaelor_pouw",
        "arguments": {
            "action": "mine",
            "miner": "@zoth_http_caller",
            "task_type": "STDP_OBSIDIAN_INDEXING"
        }
    })
    assert status == 200
    http_data = json.loads(body.decode("utf-8"))
    assert http_data["ok"] is True
    assert http_data["tool"] == "obsidian_vaelor_pouw"
    res = http_data["result"]
    assert res["ok"] is True
    assert res["action"] == "mine"
    assert res["miner"] == "@zoth_http_caller"
    assert res["rewardVlr"] > 0
    assert "blockHash" in res

    # 4. Test HTTP POST /api/mcp with standard JSON-RPC 2.0 tools/call
    status, _, body = _http_post(f"{base_url}/api/mcp", {
        "jsonrpc": "2.0",
        "id": 303,
        "method": "tools/call",
        "params": {
            "name": "obsidian_vaelor_pouw",
            "arguments": {"action": "status"}
        }
    })
    assert status == 200
    rpc_data = json.loads(body.decode("utf-8"))
    assert rpc_data.get("jsonrpc") == "2.0"
    assert rpc_data.get("id") == 303
    assert not rpc_data["result"].get("isError", False)
    rpc_res = json.loads(rpc_data["result"]["content"][0]["text"])
    assert rpc_res["ok"] is True
    assert rpc_res["action"] == "status"














