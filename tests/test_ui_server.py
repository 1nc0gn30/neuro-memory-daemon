"""Tests for Memory Studio UI Server and REST API endpoints."""

from __future__ import annotations

import json
import socket
import urllib.request
from pathlib import Path
from typing import Generator

import pytest

from neuro_memory_daemon import MemoryDaemon
from neuro_memory_daemon.ui_server import MemoryUIServer, start_server_in_thread


def get_free_port() -> int:
    """Find an available TCP port for local test server binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture
def live_server(temp_dir: Path) -> Generator[tuple[MemoryUIServer, str, MemoryDaemon], None, None]:
    """Start a live test UI server on an ephemeral port."""
    port = get_free_port()
    db_file = temp_dir / "ui_test_db.json"
    daemon = MemoryDaemon(db_path=db_file)

    # Seed initial test memories
    daemon.store("Seed memory 1: WebSocket streaming architecture", tags=["websocket", "streaming"], category="architecture")
    daemon.store("Seed memory 2: SQLite WAL concurrent locks fixed", tags=["sqlite", "wal", "fix"], category="debug")

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


def _http_get(url: str) -> tuple[int, dict[str, str], bytes]:
    """Helper to perform HTTP GET."""
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        return resp.status, dict(resp.headers), resp.read()


def _http_post(url: str, data: dict) -> tuple[int, dict[str, str], bytes]:
    """Helper to perform HTTP POST."""
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, dict(resp.headers), resp.read()


def _http_delete(url: str) -> tuple[int, dict[str, str], bytes]:
    """Helper to perform HTTP DELETE."""
    req = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(req) as resp:
        return resp.status, dict(resp.headers), resp.read()


def test_ui_server_static_html(live_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Verify GET / serves the Google Material 3 Studio UI."""
    _, base_url, _ = live_server
    status, headers, body = _http_get(f"{base_url}/")
    assert status == 200
    assert "text/html" in headers.get("Content-Type", "")
    html_text = body.decode("utf-8")
    assert "Google Neural Memory Studio" in html_text or "Neuro-Memory Studio" in html_text
    assert "synapse-canvas" in html_text or "Material 3" in html_text


def test_ui_server_health_and_stats(live_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Verify health and telemetry endpoints."""
    _, base_url, _ = live_server

    # /health
    status_h, _, body_h = _http_get(f"{base_url}/health")
    assert status_h == 200
    health = json.loads(body_h.decode("utf-8"))
    assert health["status"] == "ok"
    assert health["service"] == "neuro-memory-daemon"

    # /api/stats
    status_s, _, body_s = _http_get(f"{base_url}/api/stats")
    assert status_s == 200
    stats = json.loads(body_s.decode("utf-8"))
    assert "total_memories" in stats
    assert stats["total_memories"] >= 2


def test_ui_server_crud_and_recall(live_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Verify full memory ingestion, retrieval, recall, and deletion."""
    _, base_url, daemon = live_server

    # 1. Ingest new memory (POST /api/memories)
    new_mem = {
        "text": "Configured distributed vector consensus for subagent orchestration",
        "tags": ["agents", "consensus", "vector"],
        "category": "architecture",
        "importance": 1.4,
    }
    status_post, _, body_post = _http_post(f"{base_url}/api/memories", new_mem)
    assert status_post == 201
    created = json.loads(body_post.decode("utf-8"))
    assert created["status"] == "stored"
    mem_id = created["id"]

    # 2. List memories (GET /api/memories)
    status_list, _, body_list = _http_get(f"{base_url}/api/memories")
    assert status_list == 200
    list_data = json.loads(body_list.decode("utf-8"))
    assert list_data["total"] >= 3

    # 3. Specific memory (GET /api/memories/<id>)
    status_get, _, body_get = _http_get(f"{base_url}/api/memories/{mem_id}")
    assert status_get == 200
    fetched = json.loads(body_get.decode("utf-8"))
    assert fetched["id"] == mem_id
    assert "vector consensus" in fetched["text"]

    # 4. Recall (POST /api/recall)
    status_rec, _, body_rec = _http_post(f"{base_url}/api/recall", {"query": "vector consensus agents", "top_k": 3})
    assert status_rec == 200
    recall_data = json.loads(body_rec.decode("utf-8"))
    assert len(recall_data["recalled"]) >= 1

    # 5. Trigger synapse (POST /api/memories/<id>/trigger)
    status_trig, _, body_trig = _http_post(f"{base_url}/api/memories/{mem_id}/trigger", {})
    assert status_trig == 200

    # 6. Graph (GET /api/graph)
    status_g, _, body_g = _http_get(f"{base_url}/api/graph?format=json")
    assert status_g == 200
    graph_data = json.loads(body_g.decode("utf-8"))
    assert "nodes" in graph_data

    # 7. Sleep Consolidation (POST /api/consolidate)
    status_cons, _, body_cons = _http_post(f"{base_url}/api/consolidate", {"decay_rate": 0.05})
    assert status_cons == 200
    cons_res = json.loads(body_cons.decode("utf-8"))
    assert cons_res["status"] == "consolidated"

    # 8. Delete memory (DELETE /api/memories/<id>)
    status_del, _, body_del = _http_delete(f"{base_url}/api/memories/{mem_id}")
    assert status_del == 200
    del_res = json.loads(body_del.decode("utf-8"))
    assert del_res["status"] == "deleted"
