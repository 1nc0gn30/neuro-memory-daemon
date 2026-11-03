"""Fixture tests for the read-only everywhere memory federator.

Uses a temporary HOME. Does not touch live agent_subconscious or live grok stores.
"""

from __future__ import annotations

import json
from pathlib import Path

from neuro_memory_daemon import MemoryDaemon
from neuro_memory_daemon.everywhere import collect
from neuro_memory_daemon.ui_server import start_server_in_thread

from tests.test_ui_server import _http_get, get_free_port


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_home(home: Path) -> None:
    _write(
        home / ".grok" / "memory-v2" / "workspaces" / "demo" / "topics" / "zoth-lock.md",
        "# Zoth Lock\nWalk-away lock with scrypt hash. Super+L stays KDE.\n",
    )
    _write(
        home / ".grok" / "memory-v2" / "workspaces" / "demo" / "MEMORY.md",
        "# Workspace memory index\n\n- **Zoth Lock** (`topics/zoth-lock.md`)\n",
    )
    _write(
        home / ".grok" / "memory-v2" / "workspaces" / "demo" / "archive" / "dream_x" / "dump.md",
        "# Archived dump that should stay hidden\nsecret session transcript\n",
    )
    _write(
        home / ".grok" / "memory-v2" / "workspaces" / "demo" / "topics" / "secret-notes.md",
        "# Should be skipped because the filename has secret\n",
    )
    _write(
        home / ".hermes" / "memories" / "MEMORY.md",
        "User runs HexStrike locally and uses Shodan for network analysis.\n",
    )
    _write(home / ".hermes" / "SOUL.md", "# Hermes\nLocal-first companion.\n")
    _write(
        home / ".config" / "zothos" / "zoth-bot" / "bots" / "foundry" / "memory.md",
        "# Foundry\n\nJob: WebGen watcher\n",
    )
    _write(
        home / ".gemini" / "config" / "GEMINI.md",
        "# 1nc0gn30\nWorkspace root for projects: ~/NullAITech\n",
    )


def test_everywhere_reads_fixture_stores_and_skips_secrets(temp_dir: Path):
    home = temp_dir / "home"
    _seed_home(home)

    data = collect(home=home, daemon=None, limit=50)
    ids = {s["id"]: s for s in data["sources"]}
    assert ids["grok"]["count"] >= 2
    assert ids["hermes"]["count"] == 2
    assert ids["zoth-bot"]["count"] == 1
    assert ids["agy"]["count"] == 1
    assert ids["neuro"]["count"] == 0

    titles = [it["title"] for it in data["items"]]
    paths = [it["path"] for it in data["items"]]
    joined = " ".join(titles + paths).lower()
    assert "zoth lock" in joined
    assert "foundry" in joined.lower()
    assert "secret-notes" not in joined
    assert "dream_x" not in joined
    assert "dump.md" not in joined

    grok_only = collect(home=home, source="grok", query="lock")
    assert grok_only["total"] >= 1
    assert all(it["source"] == "grok" for it in grok_only["items"])
    assert any("lock" in (it["title"] + it["text"]).lower() for it in grok_only["items"])


def test_everywhere_includes_neuro_slice_from_daemon(temp_dir: Path):
    home = temp_dir / "home"
    _seed_home(home)
    daemon = MemoryDaemon(db_path=temp_dir / "everywhere.json")
    daemon.store("Civilization Mind lastDistillation", tags=["civilization"], category="insight")
    daemon.store("Unrelated debug note", tags=["debug"], category="debug")

    mixed = collect(home=home, daemon=daemon, limit=40)
    neuro_src = next(s for s in mixed["sources"] if s["id"] == "neuro")
    assert neuro_src["count"] == 2
    assert any(it["source"] == "neuro" for it in mixed["items"])
    assert mixed["file_count"] >= 4
    first_file = next(i for i in mixed["items"] if i["source"] != "neuro")
    first_neuro = next(i for i in mixed["items"] if i["source"] == "neuro")
    assert mixed["items"].index(first_file) < mixed["items"].index(first_neuro)

    neuro = collect(home=home, daemon=daemon, source="neuro", query="civilization")
    assert neuro["total"] >= 1
    assert all(it["source"] == "neuro" for it in neuro["items"])
    assert "civilization" in neuro["items"][0]["text"].lower()


def test_everywhere_api_on_live_server(temp_dir: Path, monkeypatch):
    home = temp_dir / "home"
    _seed_home(home)
    monkeypatch.setenv("NEURO_EVERYWHERE_HOME", str(home))

    port = get_free_port()
    daemon = MemoryDaemon(db_path=temp_dir / "ui_everywhere.json")
    daemon.store("Seed neuro engram about associative recall", tags=["recall"], category="insight")
    pub_dir = Path(__file__).resolve().parent.parent / "public"
    server = start_server_in_thread(
        host="127.0.0.1",
        port=port,
        daemon=daemon,
        public_dir=pub_dir,
    )
    try:
        status, _, body = _http_get(f"http://127.0.0.1:{port}/api/everywhere?limit=40")
        assert status == 200
        data = json.loads(body.decode("utf-8"))
        assert "sources" in data
        assert "items" in data
        source_ids = {s["id"] for s in data["sources"]}
        assert {"neuro", "grok", "hermes", "zoth-bot", "agy"} <= source_ids
        assert any(it["source"] == "grok" for it in data["items"])
        html_status, _, html = _http_get(f"http://127.0.0.1:{port}/")
        assert html_status == 200
        page = html.decode("utf-8")
        assert "everywhere" in page.lower()
        assert 'id="tab-everywhere"' in page
    finally:
        server.stop()
