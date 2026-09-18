"""Pytest fixtures and configuration for neuro-memory-daemon test suite."""

from __future__ import annotations

import socket
import tempfile
import time
from pathlib import Path
from typing import Generator

import pytest

from neuro_memory_daemon import MemoryDaemon
from neuro_memory_daemon.storage import MemoryRecord, StorageEngine, SynapseRecord
from neuro_memory_daemon.synapse_engine import DLPFCWorkingMemory, SynapseEngine
from neuro_memory_daemon.graph_builder import GraphBuilder
from neuro_memory_daemon.mcp_server import MCPServer
from neuro_memory_daemon.ui_server import start_server_in_thread, MemoryUIServer


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory that is automatically cleaned up."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def storage_in_memory() -> Generator[StorageEngine, None, None]:
    """Provide an in-memory SQLite StorageEngine."""
    engine = StorageEngine(in_memory=True)
    yield engine


@pytest.fixture
def storage_file(temp_dir: Path) -> Generator[StorageEngine, None, None]:
    """Provide a file-backed SQLite StorageEngine."""
    db_file = temp_dir / "test_memory.db"
    engine = StorageEngine(db_path=db_file)
    yield engine


@pytest.fixture
def synapse_engine(storage_in_memory: StorageEngine) -> Generator[SynapseEngine, None, None]:
    """Provide a SynapseEngine initialized with in-memory storage."""
    engine = SynapseEngine(storage=storage_in_memory)
    yield engine


@pytest.fixture
def graph_builder() -> GraphBuilder:
    """Provide a GraphBuilder instance."""
    return GraphBuilder()


@pytest.fixture
def memory_daemon(temp_dir: Path) -> Generator[MemoryDaemon, None, None]:
    """Provide a MemoryDaemon instance backed by a temporary file."""
    db_file = temp_dir / "substrate.json"
    daemon = MemoryDaemon(db_path=db_file)
    yield daemon


@pytest.fixture
def mcp_server(temp_dir: Path) -> Generator[MCPServer, None, None]:
    """Provide an MCPServer instance for testing protocol requests."""
    db_file = temp_dir / "mcp_substrate.json"
    server = MCPServer(db_path=str(db_file))
    yield server


@pytest.fixture
def sample_records() -> list[MemoryRecord]:
    """Provide a representative sample of cognitive memory records."""
    now = time.time()
    return [
        MemoryRecord(
            id="mem-1",
            agent_id="azoth",
            perspective="agent",
            text="Configured SQLite WAL mode for non-blocking concurrent queries.",
            tags=["sqlite", "wal", "database", "concurrency"],
            category="architecture",
            importance=1.4,
            access_count=6,
            last_accessed_at=now,
            created_at=now - 3600,
            decay_factor=1.5,
            immutable=True,
        ),
        MemoryRecord(
            id="mem-2",
            agent_id="hermes",
            perspective="agent",
            text="Resolved thread synchronization race condition in working memory buffer.",
            tags=["threading", "concurrency", "buffer", "fix"],
            category="debug",
            importance=1.1,
            access_count=4,
            last_accessed_at=now - 1800,
            created_at=now - 7200,
            decay_factor=1.0,
            immutable=False,
        ),
        MemoryRecord(
            id="mem-3",
            agent_id="grok",
            perspective="agent",
            text="Validated MCP JSON-RPC 2.0 tool definitions against official specification.",
            tags=["mcp", "jsonrpc", "tools", "schema"],
            category="security",
            importance=1.3,
            access_count=8,
            last_accessed_at=now,
            created_at=now - 10800,
            decay_factor=1.2,
            immutable=True,
        ),
        MemoryRecord(
            id="mem-4",
            agent_id="operator",
            perspective="user",
            text="Requested dark mode theme toggle and visual force-directed graph canvas.",
            tags=["ui", "material3", "canvas", "theme"],
            category="general",
            importance=0.8,
            access_count=2,
            last_accessed_at=now - 86400,
            created_at=now - 86400,
            decay_factor=0.9,
            immutable=False,
        ),
    ]


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

