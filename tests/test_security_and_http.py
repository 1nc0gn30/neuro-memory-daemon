"""Security, HTTP hardening, XSS, discovery, and version-parity regression tests."""

from __future__ import annotations

import http.client
import json
import re
from pathlib import Path
from typing import Generator

import pytest

from neuro_memory_daemon import MemoryDaemon, __version__
from neuro_memory_daemon.mcp_server import MCPServer
from neuro_memory_daemon.ui_server import MemoryUIServer, start_server_in_thread
from tests.test_ui_server import get_free_port


REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def hardened_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[tuple[MemoryUIServer, int, MemoryDaemon, Path], None, None]:
    fake_home = tmp_path / "home"
    vault_dir = fake_home / "Documents" / "Obsidian Vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))

    port = get_free_port()
    db_file = tmp_path / "sec_test.db"
    daemon = MemoryDaemon(db_path=db_file)
    server = start_server_in_thread(
        host="127.0.0.1",
        port=port,
        daemon=daemon,
        public_dir=REPO_ROOT / "public",
    )
    yield server, port, daemon, vault_dir
    server.stop()


def _raw_request(
    port: int,
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    body: bytes | str | None = None,
) -> tuple[int, dict[str, str], bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        hdrs = dict(headers or {})
        conn.request(method, path, body=body, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read()
        resp_headers = {k.lower(): v for k, v in resp.getheaders()}
        return resp.status, resp_headers, data
    finally:
        conn.close()


def test_loopback_host_guard_rejects_external_host_all_methods(hardened_server):
    _, port, _, _ = hardened_server
    for method in ("GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"):
        status, headers, _ = _raw_request(
            port,
            method,
            "/health",
            headers={"Host": "evil.example.invalid"},
            body=b"{}" if method in ("POST", "PUT") else None,
        )
        assert status == 403, f"Expected 403 for Host: evil.example.invalid on {method}, got {status}"
        assert headers.get("access-control-allow-origin") != "*"


def test_loopback_origin_guard_and_non_wildcard_cors(hardened_server):
    _, port, _, _ = hardened_server
    # Reject external / null / wrong-port origins across all methods
    for bad_origin in (
        "https://evil.example.invalid",
        "http://evil.example.invalid",
        "null",
        "http://127.0.0.1:9999",
    ):
        for method in ("GET", "OPTIONS", "POST", "DELETE"):
            status, headers, _ = _raw_request(
                port,
                method,
                "/api/stats",
                headers={"Origin": bad_origin, "Content-Type": "application/json"},
                body=b"{}" if method == "POST" else None,
            )
            assert status == 403, f"{method} with Origin={bad_origin} must return 403, got {status}"
            assert "access-control-allow-origin" not in headers

    # Trusted loopback origins (exact port and Studio :3000) reflect Origin + Vary: Origin (never *)
    for good_origin in (f"http://127.0.0.1:{port}", "http://127.0.0.1:3000", "http://localhost:3000"):
        status, headers, _ = _raw_request(port, "GET", "/health", headers={"Origin": good_origin})
        assert status == 200
        assert headers.get("access-control-allow-origin") == good_origin
        assert "origin" in headers.get("vary", "").lower()

        opt_status, opt_headers, _ = _raw_request(port, "OPTIONS", "/api/stats", headers={"Origin": good_origin})
        assert opt_status == 204
        assert opt_headers.get("access-control-allow-origin") == good_origin


def test_security_headers_and_stripped_server_banner(hardened_server):
    _, port, _, _ = hardened_server
    for path in ("/", "/health", "/api/stats", "/does-not-exist"):
        status, headers, _ = _raw_request(port, "GET", path)
        assert headers.get("x-frame-options") == "SAMEORIGIN"
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        csp = headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'self' http://127.0.0.1:3000 http://localhost:3000" in csp
        assert "fonts.googleapis.com" not in csp
        server_hdr = headers.get("server", "")
        assert "Python/" not in server_hdr
        assert "BaseHTTP" not in server_hdr
        assert "Neuro-Memory" in server_hdr
        assert headers.get("access-control-allow-origin") != "*"


def test_body_size_cap_413_and_malformed_json_and_headers_400(hardened_server):
    _, port, _, _ = hardened_server

    # 1. > 1 MiB body returns 413 Payload Too Large
    oversized = b'{"text":"' + (b"A" * (1_048_576 + 128)) + b'"}'
    status, _, body = _raw_request(
        port, "POST", "/api/memories",
        headers={"Content-Type": "application/json"},
        body=oversized,
    )
    assert status == 413, f"Expected 413 for >1 MiB body, got {status}"

    # 2. Invalid Content-Length returns 400 (no thread crash)
    status, _, _ = _raw_request(
        port, "POST", "/api/memories",
        headers={"Content-Type": "application/json", "Content-Length": "abc"},
    )
    assert status == 400

    # 3. Malformed JSON on REST returns 400
    status, _, _ = _raw_request(
        port, "POST", "/api/memories",
        headers={"Content-Type": "application/json"},
        body=b"{not valid json",
    )
    assert status == 400

    # 4. Malformed JSON on POST /api/mcp returns HTTP 400 + JSON-RPC -32700 Parse Error
    status, _, body = _raw_request(
        port, "POST", "/api/mcp",
        headers={"Content-Type": "application/json"},
        body=b"{truncated",
    )
    assert status == 400
    rpc = json.loads(body.decode("utf-8"))
    assert rpc["jsonrpc"] == "2.0"
    assert rpc["error"]["code"] == -32700

    # 5. Invalid numeric query params return 400 (no thread crash)
    for bad_qs in (
        "/api/memories?limit=notanint",
        "/api/memories?limit=-5",
        "/api/recall?query=test&top_k=abc",
        "/api/graph?min_weight=nan_invalid",
    ):
        status, _, _ = _raw_request(port, "GET", bad_qs)
        assert status == 400, f"Expected 400 for {bad_qs}, got {status}"


def test_obsidian_canvas_and_wiki_traversal_blocked(hardened_server):
    _, port, daemon, vault_dir = hardened_server
    escape_probes = [
        "../escaped",
        "../../tmp/pwn",
        "sub/dir",
        "bad\\slash",
        "null\x00byte",
    ]
    for probe in escape_probes:
        payload = json.dumps({"topic": probe}).encode("utf-8")
        st_c, _, _ = _raw_request(
            port, "POST", "/api/obsidian/canvas",
            headers={"Content-Type": "application/json"},
            body=payload,
        )
        assert st_c in (400, 403), f"Canvas traversal probe {probe!r} returned {st_c}"

        st_w, _, _ = _raw_request(
            port, "POST", "/api/obsidian/wiki",
            headers={"Content-Type": "application/json"},
            body=payload,
        )
        assert st_w in (400, 403), f"Wiki traversal probe {probe!r} returned {st_w}"

    # Verify MCP direct handlers also block traversal
    mcp = MCPServer(daemon=daemon)
    for tool_name in ("obsidian_canvas_generate", "obsidian_wiki_synthesize"):
        resp = mcp.handle_request({
            "jsonrpc": "2.0", "id": 999, "method": "tools/call",
            "params": {"name": tool_name, "arguments": {"topic": "../../escaped"}}
        })
        assert resp["result"].get("isError") is True

    # Ensure no escaped canvas was created in parent of vault_dir
    assert not list(vault_dir.parent.glob("*.canvas"))


def test_discovery_files_and_static_ui_security_invariants(hardened_server):
    _, port, _, _ = hardened_server

    # Discovery manifests served with 200
    st_llms, _, llms_body = _raw_request(port, "GET", "/llms.txt")
    assert st_llms == 200
    assert b"Neal Frazier Tech" in llms_body

    st_mcp, _, mcp_body = _raw_request(port, "GET", "/.well-known/mcp.json")
    assert st_mcp == 200
    mcp_manifest = json.loads(mcp_body.decode("utf-8"))
    assert mcp_manifest["version"] == "2.9.0"
    assert mcp_manifest["toolCount"] == 21

    st_sm, _, sm_body = _raw_request(port, "GET", "/sitemap.xml")
    assert st_sm == 200
    assert b"/api/health" not in sm_body
    assert b"/api/stats" not in sm_body

    st_og, og_hdrs, og_body = _raw_request(port, "GET", "/og-image.png")
    assert st_og == 200
    assert og_hdrs.get("content-type", "").startswith("image/png")
    assert og_body[:8] == b"\x89PNG\r\n\x1a\n"

    # Static UI invariants on public/index.html
    html = (REPO_ROOT / "public" / "index.html").read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in html
    assert "fonts.gstatic.com" not in html
    assert "sales-funnel-banner" not in html
    assert "openLicenseModal" not in html
    assert "openSolanaPay" not in html
    assert "41,750" not in html
    assert html.count("https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X") == 1
    assert "onclick=\"filterByTag(" not in html
    assert "t.innerHTML = `<span>${icon}</span> <span>${msg}</span>`" not in html
    assert "v2.9.0" in html
    assert "https://neuro-memory.nullai.tech/og-image.png" in html

    # Unified version 2.9.0 & Apache-2.0 license parity
    assert __version__ == "2.9.0"
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "2.9.0"' in pyproject
    assert 'Apache-2.0' in pyproject
    pkg = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    assert pkg["version"] == "2.9.0"
    assert pkg["license"] == "Apache-2.0"
    assert "Neal Frazier Tech" in pkg["author"]
