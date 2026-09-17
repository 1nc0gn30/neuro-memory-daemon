"""Tests for Model Context Protocol (MCP) server implementation."""

from __future__ import annotations

import json
from neuro_memory_daemon.mcp_server import MCPServer


def test_mcp_initialize(mcp_server: MCPServer):
    """Verify MCP initialize handshake response."""
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }
    resp = mcp_server.handle_request(req)
    assert resp is not None
    assert resp["id"] == 1
    assert "result" in resp
    assert resp["result"]["protocolVersion"] == "2024-11-05"
    assert resp["result"]["serverInfo"]["name"] == "neuro-memory-daemon"


def test_mcp_tools_list(mcp_server: MCPServer):
    """Verify all required cognitive memory tools are registered in tools/list."""
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    resp = mcp_server.handle_request(req)
    assert resp is not None
    assert "result" in resp
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]

    expected = [
        "memory_store",
        "memory_recall",
        "memory_search",
        "memory_graph",
        "memory_consolidate",
        "memory_stats",
        "memory_diagnostics",
    ]
    for exp in expected:
        assert exp in tool_names


def test_mcp_tools_call_lifecycle(mcp_server: MCPServer):
    """Verify full tool execution lifecycle over JSON-RPC."""
    # 1. memory_store
    store_req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "memory_store",
            "arguments": {
                "text": "Autonomous agents require persistent episodic and semantic recall substrates",
                "tags": ["agents", "mcp", "memory", "subagent"],
                "category": "architecture",
                "importance": 1.5,
            },
        },
    }
    store_resp = mcp_server.handle_request(store_req)
    assert store_resp is not None
    assert not store_resp["result"].get("isError", False)
    content_text = store_resp["result"]["content"][0]["text"]
    assert "Stored successfully" in content_text or "id" in content_text.lower()

    # 2. memory_recall
    recall_req = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "memory_recall",
            "arguments": {"query": "persistent agent memory", "top_k": 3},
        },
    }
    recall_resp = mcp_server.handle_request(recall_req)
    assert recall_resp is not None
    assert not recall_resp["result"].get("isError", False)

    # 3. memory_search
    search_req = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {
            "name": "memory_search",
            "arguments": {"query": "autonomous", "limit": 5},
        },
    }
    search_resp = mcp_server.handle_request(search_req)
    assert search_resp is not None
    assert not search_resp["result"].get("isError", False)

    # 4. memory_graph
    graph_req = {
        "jsonrpc": "2.0",
        "id": 13,
        "method": "tools/call",
        "params": {
            "name": "memory_graph",
            "arguments": {"format": "json"},
        },
    }
    graph_resp = mcp_server.handle_request(graph_req)
    assert graph_resp is not None
    assert not graph_resp["result"].get("isError", False)

    # 5. memory_consolidate
    cons_req = {
        "jsonrpc": "2.0",
        "id": 14,
        "method": "tools/call",
        "params": {
            "name": "memory_consolidate",
            "arguments": {"decay_rate": 0.05},
        },
    }
    cons_resp = mcp_server.handle_request(cons_req)
    assert cons_resp is not None
    assert not cons_resp["result"].get("isError", False)

    # 6. memory_stats
    stats_req = {
        "jsonrpc": "2.0",
        "id": 15,
        "method": "tools/call",
        "params": {
            "name": "memory_stats",
            "arguments": {"detailed": True},
        },
    }
    stats_resp = mcp_server.handle_request(stats_req)
    assert stats_resp is not None
    assert not stats_resp["result"].get("isError", False)

    # 7. memory_diagnostics
    diag_req = {
        "jsonrpc": "2.0",
        "id": 16,
        "method": "tools/call",
        "params": {
            "name": "memory_diagnostics",
            "arguments": {"verbose": True},
        },
    }
    diag_resp = mcp_server.handle_request(diag_req)
    assert diag_resp is not None
    assert not diag_resp["result"].get("isError", False)


def test_mcp_unknown_tool(mcp_server: MCPServer):
    """Verify calling an unknown tool returns an error response."""
    req = {
        "jsonrpc": "2.0",
        "id": 99,
        "method": "tools/call",
        "params": {"name": "non_existent_tool", "arguments": {}},
    }
    resp = mcp_server.handle_request(req)
    assert resp is not None
    assert resp["result"].get("isError", False) is True
