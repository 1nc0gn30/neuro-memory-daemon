"""Tests for GraphBuilder and synaptic topology visualization engines."""

from __future__ import annotations

from neuro_memory_daemon.storage import MemoryRecord, SynapseRecord
from neuro_memory_daemon.graph_builder import (
    GraphBuilder,
    escape_mermaid_label,
    sanitize_mermaid_id,
)


def test_sanitize_mermaid_id():
    """Verify ID sanitization for Mermaid syntax compliance."""
    assert sanitize_mermaid_id("mem-1234-abcd") == "mem_1234_abcd"
    assert sanitize_mermaid_id("123leading") == "n_123leading"
    assert sanitize_mermaid_id("tag:auth/jwt") == "tag_auth_jwt"


def test_escape_mermaid_label():
    """Verify label escaping for special characters."""
    raw = 'Memory with "quotes", [brackets], (parens), and {braces}'
    escaped = escape_mermaid_label(raw)
    assert '"' not in escaped
    assert "#quot;" in escaped
    assert "[" not in escaped


def test_graph_builder_mermaid(graph_builder: GraphBuilder, sample_records: list[MemoryRecord]):
    """Test generation of Mermaid flowchart syntax."""
    synapses = [
        SynapseRecord(source="sqlite", target="wal", weight=0.85),
        SynapseRecord(source="mcp", target="jsonrpc", weight=0.75),
    ]

    mermaid_str = graph_builder.to_mermaid(
        memories=sample_records,
        synapses=synapses,
        active_memory_ids={"mem-1"},
        group_by_category=True,
    )

    assert "flowchart TD" in mermaid_str
    assert "subgraph" in mermaid_str
    assert "classDef memoryNode" in mermaid_str
    assert "classDef activeNode" in mermaid_str
    assert "mem_mem_1" in mermaid_str


def test_graph_builder_adjacency(graph_builder: GraphBuilder, sample_records: list[MemoryRecord]):
    """Test JSON adjacency graph generation and metrics."""
    synapses = [
        SynapseRecord(source="sqlite", target="wal", weight=0.85),
        SynapseRecord(source="concurrency", target="threading", weight=0.6),
    ]

    graph_data = graph_builder.build_adjacency_graph(
        memories=sample_records,
        synapses=synapses,
        active_memory_ids={"mem-1"},
    )

    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert "metrics" in graph_data
    assert graph_data["metrics"]["total_nodes"] > 0
    assert graph_data["metrics"]["total_edges"] > 0

    # Test knowledge hubs ranking
    hubs = graph_builder.find_knowledge_hubs(graph_data, top_k=3)
    assert len(hubs) > 0
    assert "degree" in hubs[0]


def test_graph_builder_associative_path(graph_builder: GraphBuilder):
    """Test Dijkstra minimum resistance associative pathway discovery."""
    synapses = [
        SynapseRecord(source="sqlite", target="wal", weight=0.9),
        SynapseRecord(source="wal", target="concurrency", weight=0.8),
    ]

    graph_data = graph_builder.build_adjacency_graph(
        memories=[],
        synapses=synapses,
    )

    # Path from tag_sqlite to tag_concurrency via tag_wal
    path = graph_builder.find_associative_path(graph_data, "tag_sqlite", "tag_concurrency")
    assert path is not None
    assert len(path) == 2
    assert path[0]["from"] == "tag_sqlite"
    assert path[0]["to"] == "tag_wal"
    assert path[1]["to"] == "tag_concurrency"
