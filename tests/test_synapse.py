"""Tests for SynapseEngine, cognitive neuroscience algorithms, and STDP."""

from __future__ import annotations

import time

from neuro_memory_daemon.storage import MemoryRecord, StorageEngine
from neuro_memory_daemon.synapse_engine import (
    DLPFCWorkingMemory,
    SynapseEngine,
    compute_sparse_cosine_similarity,
    compute_tf,
    tokenize,
)


def test_tokenize_and_tf():
    """Verify tokenizer splits words and removes stopwords."""
    tokens = tokenize("The SQLiteDatabase performs WAL transaction logging efficiently")
    assert "the" not in tokens
    assert "sqlite" in tokens
    assert "database" in tokens
    assert "wal" in tokens
    assert "transaction" in tokens

    tf = compute_tf(tokens)
    assert len(tf) > 0
    assert all(v > 0 for v in tf.values())


def test_sparse_cosine_similarity():
    """Verify sparse cosine similarity between term vectors."""
    vec1 = {"sqlite": 1.0, "wal": 1.0, "performance": 0.8}
    vec2 = {"sqlite": 0.9, "wal": 1.1, "performance": 0.7}
    vec3 = {"completely": 1.0, "unrelated": 1.0}

    high_sim = compute_sparse_cosine_similarity(vec1, vec2)
    zero_sim = compute_sparse_cosine_similarity(vec1, vec3)

    assert high_sim > 0.9
    assert zero_sim == 0.0


def test_dlpfc_working_memory_lru():
    """Verify DLPFC Working Memory capacity and LRU eviction."""
    wm = DLPFCWorkingMemory(capacity=3)
    assert wm.capacity == 3
    assert wm.size == 0

    m1 = MemoryRecord(id="m1", text="Memory 1")
    m2 = MemoryRecord(id="m2", text="Memory 2")
    m3 = MemoryRecord(id="m3", text="Memory 3")
    m4 = MemoryRecord(id="m4", text="Memory 4")

    wm.put(m1)
    wm.put(m2)
    wm.put(m3)
    assert wm.size == 3
    assert wm.contains("m1")

    # Access m1 to make it most recently used
    wm.get("m1")

    # Insert m4 -> should evict m2 (oldest)
    evicted = wm.put(m4)
    assert evicted is not None
    assert evicted.id == "m2"
    assert wm.contains("m1")
    assert wm.contains("m3")
    assert wm.contains("m4")
    assert not wm.contains("m2")


def test_stdp_synapse_reinforcement(synapse_engine: SynapseEngine):
    """Test Spike-Timing-Dependent Plasticity (STDP) weight reinforcement."""
    se = synapse_engine

    # Initial reinforcement
    w1 = se.reinforce_synapse("database", "indexing", delta_t=1.0)
    assert w1 > 0.05

    # Secondary reinforcement should increase weight (Long-Term Potentiation)
    w2 = se.reinforce_synapse("database", "indexing", delta_t=0.5)
    assert w2 > w1

    # Associated nodes lookup
    assoc = se.get_associated_nodes("database")
    assert len(assoc) >= 1
    assert assoc[0][0] == "indexing"


def test_ca3_pattern_completion(synapse_engine: SynapseEngine):
    """Test CA3 auto-associative pattern completion."""
    se = synapse_engine

    # Establish cluster of synapses: react -> hooks, state, virtualdom
    se.reinforce_synapse("react", "hooks", delta_t=0.0)
    se.reinforce_synapse("react", "state", delta_t=0.0)
    se.reinforce_synapse("hooks", "virtualdom", delta_t=0.0)

    # Query with partial cue 'react'
    completion = se.pattern_completion(["react"])
    assert "original_cues" in completion
    assert "hooks" in completion["completed_tags"] or "state" in completion["completed_tags"]
    assert completion["completion_confidence"] > 0.0


def test_ca1_pattern_separation(synapse_engine: SynapseEngine):
    """Test Dentate Gyrus / CA1 pattern separation to prevent interference."""
    se = synapse_engine
    existing_mems = [
        MemoryRecord(id="e1", text="Configured PostgreSQL connection pool with 20 max connections", tags=["postgres", "database"]),
    ]

    # Similar but distinct memory
    new_text = "Configured MySQL connection pool with 50 max connections"
    dist_score, disambig_tags = se.pattern_separation(new_text, ["mysql", "database"], candidate_pool=existing_mems)

    assert 0.0 <= dist_score <= 1.0
    assert "mysql" in disambig_tags


def test_ebbinghaus_retention_and_consolidation(synapse_engine: SynapseEngine):
    """Test exponential forgetting calculations and systems consolidation."""
    se = synapse_engine
    now = time.time()

    fresh_mem = MemoryRecord(id="f1", text="Fresh memory", last_accessed_at=now, created_at=now, immutable=False)
    old_mem = MemoryRecord(id="o1", text="Old memory", last_accessed_at=now - (86400 * 30), created_at=now - (86400 * 30), immutable=False)
    immutable_mem = MemoryRecord(id="i1", text="Immutable memory", last_accessed_at=now - (86400 * 100), immutable=True)

    r_fresh = se.calculate_retention(fresh_mem, current_time=now)
    r_old = se.calculate_retention(old_mem, current_time=now)
    r_imm = se.calculate_retention(immutable_mem, current_time=now)

    assert r_fresh > 0.9
    assert r_old < r_fresh
    assert r_imm == 1.0

    # Pruning candidates
    candidates = se.identify_pruning_candidates([fresh_mem, old_mem, immutable_mem], retention_threshold=0.5, current_time=now)
    assert old_mem in candidates
    assert fresh_mem not in candidates
    assert immutable_mem not in candidates


def test_unified_cognitive_recall(synapse_engine: SynapseEngine, sample_records: list[MemoryRecord]):
    """Test end-to-end cognitive recall with ranking."""
    se = synapse_engine
    for r in sample_records:
        se.storage.save_memory(r)

    # Reinforce synapses between sqlite and wal
    se.reinforce_synapse("sqlite", "wal", delta_t=0.0)

    # Perform recall
    results = se.recall("sqlite concurrency wal", top_k=3)
    assert len(results) >= 1
    top_result = results[0]
    assert top_result.memory.id == "mem-1"
    assert top_result.score > 0.1
    assert "sqlite" in top_result.memory.tags
