"""Tests for sleep-replay memory consolidation and schema clustering."""

import time

from neuro_memory_daemon.sleep_replay import (
    SemanticSchemaCluster,
    SleepReplayReport,
    run_sleep_replay_consolidation,
)
from neuro_memory_daemon.storage import MemoryRecord, StorageEngine
from neuro_memory_daemon.synapse_engine import SynapseEngine


def test_empty_sleep_replay():
    storage = StorageEngine(in_memory=True)
    engine = SynapseEngine(storage=storage)
    report = run_sleep_replay_consolidation(engine)
    assert isinstance(report, SleepReplayReport)
    assert report.replayed_memories_count == 0
    assert report.consolidated_count == 0


def test_sleep_replay_consolidation_and_schemata():
    storage = StorageEngine(in_memory=True)
    engine = SynapseEngine(storage=storage)

    now = time.time()
    # Seed 3 related episodic memories
    mem1 = MemoryRecord(
        id="mem-vec-1",
        text="Vector databases use HNSW skip-graphs for approximate nearest neighbors.",
        tags=["vector", "database", "hnsw"],
        importance=1.5,
        category="episodic",
        created_at=now - 3600,
        last_accessed_at=now,
    )
    mem2 = MemoryRecord(
        id="mem-vec-2",
        text="Cosine distance measures angular alignment in high-dimensional vector embeddings.",
        tags=["vector", "similarity", "math"],
        importance=1.2,
        category="episodic",
        created_at=now - 3600,
        last_accessed_at=now,
    )
    mem3 = MemoryRecord(
        id="mem-vec-3",
        text="Product quantization compresses vector floats into 8-bit cluster centroid indices.",
        tags=["vector", "compression", "quantization"],
        importance=1.0,
        category="episodic",
        created_at=now - 3600,
        last_accessed_at=now,
    )

    storage.save_memory(mem1)
    storage.save_memory(mem2)
    storage.save_memory(mem3)

    # Simulate access count for mem1 and mem2
    for _ in range(4):
        storage.record_access(mem1.id, timestamp=now)
        storage.record_access(mem2.id, timestamp=now)

    report = run_sleep_replay_consolidation(
        engine,
        replay_passes=2,
        now=now,
    )

    assert report.replayed_memories_count > 0
    assert report.consolidated_count >= 2
    assert report.new_synapses_forged > 0
    assert len(report.schemata_synthesized) >= 1
    assert any(s["name"] == "Schema::Vector" for s in report.schemata_synthesized)

    # Verify mem1 is consolidated
    updated_mem1 = storage.get_memory(mem1.id)
    assert updated_mem1 is not None
    assert updated_mem1.decay_factor > 1.0


def test_sleep_replay_prunes_decayed_memories():
    storage = StorageEngine(in_memory=True)
    engine = SynapseEngine(storage=storage)

    t_ancient = 1000000.0  # long ago
    t_now = t_ancient + (86400.0 * 30)  # 30 days later

    # Create low-importance ephemeral trace
    decayed = MemoryRecord(
        id="mem-decayed-1",
        text="Temporary clipboard paste from yesterday.",
        tags=["temp"],
        importance=0.1,
        category="episodic",
        immutable=False,
        created_at=t_ancient,
        last_accessed_at=t_ancient,
    )

    # Create important memory
    durable = MemoryRecord(
        id="mem-durable-1",
        text="Core system architectural decision: use SQLite with WAL mode.",
        tags=["arch"],
        importance=1.5,
        category="semantic",
        immutable=True,
        created_at=t_ancient,
        last_accessed_at=t_ancient,
    )

    storage.save_memory(decayed)
    storage.save_memory(durable)

    report = run_sleep_replay_consolidation(
        engine,
        min_retention_threshold=0.30,
        now=t_now,
    )

    assert report.pruned_decayed_count >= 1
    assert storage.get_memory(decayed.id) is None
    assert storage.get_memory(durable.id) is not None
