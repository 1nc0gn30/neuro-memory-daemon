"""Tests for StorageEngine and memory/synapse data models."""

from __future__ import annotations

import time
from pathlib import Path

from neuro_memory_daemon.storage import (
    MemoryRecord,
    StorageEngine,
    SynapseRecord,
    calculate_shannon_entropy,
    normalize_tags,
)


def test_calculate_shannon_entropy():
    """Verify Shannon entropy calculation."""
    assert calculate_shannon_entropy("") == 0.0
    assert calculate_shannon_entropy("a") == 0.0
    
    # Low entropy (repetitive)
    low = calculate_shannon_entropy("aaaaaaaaaaaaaaaa")
    # High entropy (diverse)
    high = calculate_shannon_entropy("Quantum algorithm executing distributed consensus on hash table")
    assert high > low
    assert 0.0 <= high <= 1.0


def test_normalize_tags():
    """Verify tag cleaning, deduplication, and case normalization."""
    raw = ["#AI", "  ML ", "ai", "Database", "#ml"]
    cleaned = normalize_tags(raw)
    assert cleaned == ["ai", "ml", "database"]

    # String input
    from_str = normalize_tags("#sqlite, #wal, database")
    assert from_str == ["sqlite", "wal", "database"]


def test_memory_record_serialization():
    """Verify MemoryRecord serialization and deserialization."""
    rec = MemoryRecord(
        id="mem-test-1",
        agent_id="azoth",
        perspective="agent",
        text="Sample memory text",
        tags=["#test", "Unit"],
        category="architecture",
        importance=1.5,
        access_count=3,
        immutable=True,
    )
    assert rec.tags == ["test", "unit"]
    assert rec.entropy_score > 0.0

    d = rec.to_dict()
    restored = MemoryRecord.from_dict(d)
    assert restored.id == rec.id
    assert restored.text == rec.text
    assert restored.tags == ["test", "unit"]
    assert restored.importance == 1.5
    assert restored.immutable is True


def test_synapse_record_serialization():
    """Verify SynapseRecord serialization and deserialization."""
    syn = SynapseRecord(source="sqlite", target="wal", weight=0.85, co_occurrence_count=5)
    d = syn.to_dict()
    assert d["weight"] == 0.85
    assert d["co_occurrence_count"] == 5

    restored = SynapseRecord.from_dict(d)
    assert restored.source == "sqlite"
    assert restored.target == "wal"
    assert restored.weight == 0.85


def test_storage_engine_crud(storage_in_memory: StorageEngine):
    """Test full CRUD operations in StorageEngine."""
    db = storage_in_memory

    # Create / Save
    rec = MemoryRecord(
        id="mem-1",
        agent_id="azoth",
        text="First persistent memory record.",
        tags=["first", "test"],
        category="general",
    )
    saved_id = db.save_memory(rec)
    assert saved_id == "mem-1"

    # Read
    fetched = db.get_memory("mem-1")
    assert fetched is not None
    assert fetched.text == "First persistent memory record."
    assert fetched.tags == ["first", "test"]

    # Update
    updated = db.update_memory("mem-1", text="Updated text.", importance=1.8)
    assert updated is not None
    assert updated.text == "Updated text."
    assert updated.importance == 1.8

    # Verify update in DB
    refetched = db.get_memory("mem-1")
    assert refetched.text == "Updated text."
    assert refetched.importance == 1.8

    # Delete
    assert db.delete_memory("mem-1") is True
    assert db.get_memory("mem-1") is None
    assert db.delete_memory("mem-1") is False


def test_storage_engine_filtering_and_sorting(storage_in_memory: StorageEngine, sample_records: list[MemoryRecord]):
    """Test memory listing with category, agent, tag filters and sorting."""
    db = storage_in_memory
    for r in sample_records:
        db.save_memory(r)

    assert db.count_memories() == 4

    # Filter by category
    arch_mems = db.list_memories(category="architecture")
    assert len(arch_mems) == 1
    assert arch_mems[0].id == "mem-1"

    # Filter by tag
    concurrency_mems = db.list_memories(tag="concurrency")
    assert len(concurrency_mems) == 2

    # Filter by agent
    grok_mems = db.list_memories(agent_id="grok")
    assert len(grok_mems) == 1
    assert grok_mems[0].agent_id == "grok"

    # Sorting
    sorted_by_imp = db.list_memories(sort_by="importance", ascending=False)
    assert sorted_by_imp[0].importance >= sorted_by_imp[1].importance


def test_storage_engine_search_text(storage_in_memory: StorageEngine, sample_records: list[MemoryRecord]):
    """Test SQL LIKE full-text search."""
    db = storage_in_memory
    for r in sample_records:
        db.save_memory(r)

    results = db.search_text("WAL mode")
    assert len(results) == 1
    assert results[0].id == "mem-1"

    no_results = db.search_text("NonExistentToken9999")
    assert len(no_results) == 0


def test_storage_engine_prune_immutable(storage_in_memory: StorageEngine):
    """Verify that immutable memories are protected from pruning."""
    db = storage_in_memory
    m1 = MemoryRecord(id="m1", text="Ephemeral note", immutable=False)
    m2 = MemoryRecord(id="m2", text="Permanent fact", immutable=True)

    db.save_memory(m1)
    db.save_memory(m2)

    deleted = db.prune_memories(["m1", "m2"])
    assert deleted == 1
    assert db.get_memory("m1") is None
    assert db.get_memory("m2") is not None


def test_storage_engine_synapses(storage_in_memory: StorageEngine):
    """Test synapse record storage, reinforcement, and retrieval."""
    db = storage_in_memory

    # Save initial synapse
    syn = db.save_synapse(source="sqlite", target="wal", weight=0.3)
    assert syn.weight == 0.3

    fetched = db.get_synapse("sqlite", "wal")
    assert fetched is not None
    assert fetched.weight == 0.3

    # Reinforce existing synapse
    reinforced = db.save_synapse(source="sqlite", target="wal", weight=0.7, co_occur_delta=1)
    assert reinforced.weight == 0.7

    # Get synapses for node
    node_syns = db.get_synapses_for_node("sqlite")
    assert len(node_syns) >= 1

    # Prune below threshold
    db.save_synapse(source="temp_a", target="temp_b", weight=0.005)
    pruned_count = db.prune_synapses(min_weight=0.01)
    assert pruned_count >= 1
    assert db.get_synapse("temp_a", "temp_b") is None
