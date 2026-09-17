"""Comprehensive unit test suite for neuro-memory-daemon core modules:
- compat.py
- storage.py
- synapse_engine.py
- graph_builder.py
"""

import os
import re
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from neuro_memory_daemon.compat import (
    atomic_replace,
    atomic_write,
    ensure_dir,
    get_default_data_dir,
    is_linux,
    is_macos,
    is_termux,
    is_windows,
    normalize_path,
    safe_read_json,
    safe_read_text,
    safe_write_json,
    safe_write_text,
)
from neuro_memory_daemon.graph_builder import (
    GraphBuilder,
    escape_mermaid_label,
    sanitize_mermaid_id,
)
from neuro_memory_daemon.storage import (
    MemoryRecord,
    StorageEngine,
    SynapseRecord,
    calculate_shannon_entropy,
    normalize_tags,
)
from neuro_memory_daemon.synapse_engine import (
    DLPFCWorkingMemory,
    RecallResult,
    SynapseEngine,
    compute_sparse_cosine_similarity,
    compute_tf,
    tokenize,
)


class TestCompat(unittest.TestCase):
    """Test cross-platform compatibility layer."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="neuro_compat_test_"))

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_platform_detection(self) -> None:
        # One of windows, linux, macos should be true on any test runner
        has_platform = is_windows() or is_linux() or is_macos()
        self.assertTrue(has_platform)
        self.assertIsInstance(is_termux(), bool)

    def test_normalize_path(self) -> None:
        p = normalize_path("test.txt", base_dir=self.temp_dir)
        self.assertTrue(p.is_absolute())
        self.assertEqual(p.parent, self.temp_dir.resolve())

    def test_atomic_write_and_safe_read(self) -> None:
        target = self.temp_dir / "subdir" / "atomic.txt"
        test_text = "Neuro-Associative Memory Trace: 🧠 Alpha-10"
        written_path = atomic_write(target, test_text, encoding="utf-8")
        self.assertTrue(written_path.exists())

        read_back = safe_read_text(target)
        self.assertEqual(read_back, test_text)

    def test_atomic_replace(self) -> None:
        src = self.temp_dir / "src.txt"
        dst = self.temp_dir / "dst.txt"
        src.write_text("source content", encoding="utf-8")
        dst.write_text("old content", encoding="utf-8")

        atomic_replace(src, dst)
        self.assertEqual(dst.read_text(encoding="utf-8"), "source content")
        self.assertFalse(src.exists())

    def test_json_safe_io(self) -> None:
        json_file = self.temp_dir / "data.json"
        data = {"key": "value", "list": [1, 2, 3], "nested": {"a": True}}
        safe_write_json(json_file, data)
        loaded = safe_read_json(json_file)
        self.assertEqual(loaded, data)

    def test_get_default_data_dir(self) -> None:
        data_dir = get_default_data_dir("test_app_dir")
        self.assertTrue(data_dir.exists())


class TestStorage(unittest.TestCase):
    """Test SQLite-backed persistent memory and synapse storage."""

    def setUp(self) -> None:
        self.storage = StorageEngine(in_memory=True)

    def tearDown(self) -> None:
        self.storage.close()

    def test_save_and_retrieve_memory(self) -> None:
        record = MemoryRecord(
            text="Implement zero-trust OAuth token rotation mechanism",
            tags=["security", "oauth", "jwt"],
            category="security",
            importance=0.95,
            perspective="agent",
            agent_id="agent_1",
            immutable=True,
            metadata={"priority": "high"},
        )
        mem_id = self.storage.save_memory(record)
        retrieved = self.storage.get_memory(mem_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, mem_id)
        self.assertEqual(retrieved.category, "security")
        self.assertTrue(retrieved.immutable)
        self.assertEqual(retrieved.metadata.get("priority"), "high")
        self.assertGreater(retrieved.entropy_score, 0.0)

    def test_list_and_filter_memories(self) -> None:
        self.storage.save_memory(
            MemoryRecord(text="Mem 1", tags=["tag_a"], category="debug", agent_id="ag1")
        )
        self.storage.save_memory(
            MemoryRecord(text="Mem 2", tags=["tag_b"], category="security", agent_id="ag1")
        )
        self.storage.save_memory(
            MemoryRecord(text="Mem 3", tags=["tag_a"], category="debug", agent_id="ag2")
        )

        self.assertEqual(self.storage.count_memories(), 3)
        self.assertEqual(self.storage.count_memories(agent_id="ag1"), 2)
        self.assertEqual(self.storage.count_memories(category="debug"), 2)

        tag_a_mems = self.storage.list_memories(tag="tag_a")
        self.assertEqual(len(tag_a_mems), 2)

    def test_record_access(self) -> None:
        m = MemoryRecord(text="Access test trace")
        self.storage.save_memory(m)
        self.assertEqual(m.access_count, 0)

        updated = self.storage.record_access(m.id)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.access_count, 1)

    def test_prune_respects_immutable(self) -> None:
        m_mutable = self.storage.save_memory(MemoryRecord(text="Mutable", immutable=False))
        m_immutable = self.storage.save_memory(MemoryRecord(text="Protected", immutable=True))

        deleted = self.storage.prune_memories([m_mutable, m_immutable])
        self.assertEqual(deleted, 1)
        self.assertIsNone(self.storage.get_memory(m_mutable))
        self.assertIsNotNone(self.storage.get_memory(m_immutable))

    def test_synapse_crud(self) -> None:
        self.storage.save_synapse("alpha", "beta", weight=0.85)
        syn = self.storage.get_synapse("alpha", "beta")
        self.assertIsNotNone(syn)
        self.assertAlmostEqual(syn.weight, 0.85, places=2)

        synapses_for_alpha = self.storage.get_synapses_for_node("alpha")
        self.assertEqual(len(synapses_for_alpha), 1)

        pruned = self.storage.prune_synapses(min_weight=0.9)
        self.assertEqual(pruned, 1)

    def test_journal_export_import(self) -> None:
        self.storage.save_memory(MemoryRecord(text="Trace 1", tags=["t1"]))
        self.storage.save_synapse("t1", "t2", weight=0.7)

        journal = self.storage.export_journal()
        self.assertEqual(journal["memories_count"], 1)
        self.assertEqual(journal["synapses_count"], 1)

        new_storage = StorageEngine(in_memory=True)
        imported = new_storage.import_journal(journal)
        self.assertEqual(imported, 1)
        self.assertEqual(new_storage.count_memories(), 1)
        new_storage.close()


class TestSynapseEngine(unittest.TestCase):
    """Test cognitive neuroscience algorithms: STDP, CA3/CA1, DLPFC, Ebbinghaus, TF-IDF."""

    def setUp(self) -> None:
        self.storage = StorageEngine(in_memory=True)
        self.engine = SynapseEngine(self.storage, working_memory_capacity=3)

    def tearDown(self) -> None:
        self.storage.close()

    def test_stdp_reinforcement(self) -> None:
        w1 = self.engine.reinforce_synapse("neural", "synapse", delta_t=0.0)
        self.assertGreater(w1, 0.0)

        # Successive reinforcement should potentiate weight
        w2 = self.engine.reinforce_synapse("neural", "synapse", delta_t=0.0)
        self.assertGreater(w2, w1)

    def test_ca3_pattern_completion(self) -> None:
        self.engine.record_coactivation(["quantum", "entanglement", "qubit", "teleportation"])
        completion = self.engine.pattern_completion(["quantum"])
        self.assertIn("quantum", completion["original_cues"])
        self.assertTrue(any(tag in completion["completed_tags"] for tag in ["entanglement", "qubit", "teleportation"]))

    def test_ca1_pattern_separation(self) -> None:
        self.storage.save_memory(
            MemoryRecord(text="Configured PostgreSQL connection pool on port 5432", tags=["postgres", "database"])
        )

        score_dup, _ = self.engine.pattern_separation(
            "Configured PostgreSQL connection pool on port 5432",
            ["postgres"]
        )
        score_diff, disambig = self.engine.pattern_separation(
            "Synthesized graphene nanoribbons using chemical vapor deposition",
            ["graphene", "materials"]
        )
        self.assertGreater(score_diff, score_dup)
        self.assertEqual(score_dup, 0.0)

    def test_dlpfc_working_memory_lru(self) -> None:
        wm = DLPFCWorkingMemory(capacity=2)
        m1 = MemoryRecord(text="Mem 1")
        m2 = MemoryRecord(text="Mem 2")
        m3 = MemoryRecord(text="Mem 3")

        wm.put(m1)
        wm.put(m2)
        self.assertEqual(wm.size, 2)
        self.assertTrue(wm.contains(m1.id))

        # Adding m3 evicts oldest (m1)
        evicted = wm.put(m3)
        self.assertIsNotNone(evicted)
        self.assertEqual(evicted.id, m1.id)
        self.assertFalse(wm.contains(m1.id))
        self.assertTrue(wm.contains(m2.id))
        self.assertTrue(wm.contains(m3.id))

    def test_ebbinghaus_retention(self) -> None:
        mem = MemoryRecord(text="Trace", access_count=0, importance=1.0)
        now = time.time()
        ret_fresh = self.engine.calculate_retention(mem, current_time=now)
        self.assertAlmostEqual(ret_fresh, 1.0, places=2)

        # 10 days later without access
        ret_decayed = self.engine.calculate_retention(mem, current_time=now + 86400 * 10)
        self.assertLess(ret_decayed, ret_fresh)

    def test_unified_recall(self) -> None:
        self.storage.save_memory(
            MemoryRecord(
                text="Asynchronous event loop event dispatching in asyncio reactor",
                tags=["asyncio", "python", "concurrency"],
                category="architecture",
                importance=0.9,
            )
        )
        self.storage.save_memory(
            MemoryRecord(
                text="Securing API gateway with TLS 1.3 mutual authentication",
                tags=["security", "tls", "gateway"],
                category="security",
                importance=0.8,
            )
        )

        results = self.engine.recall("How does asyncio concurrency event loop work?")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertEqual(top.memory.category, "architecture")
        self.assertGreater(top.score, 0.3)


class TestGraphBuilder(unittest.TestCase):
    """Test Mermaid flowchart and JSON adjacency graph generation."""

    def setUp(self) -> None:
        self.builder = GraphBuilder()
        self.memories = [
            MemoryRecord(
                text="Architectural design of synaptic cognitive daemon",
                tags=["architecture", "synapse", "cognitive"],
                category="architecture",
                importance=0.9,
            ),
            MemoryRecord(
                text="Fix race condition in thread synchronization lock",
                tags=["debug", "threading", "lock"],
                category="debug",
                importance=0.7,
            ),
        ]
        self.synapses = [
            SynapseRecord(source="synapse", target="cognitive", weight=0.88),
            SynapseRecord(source="threading", target="lock", weight=0.75),
        ]

    def test_mermaid_generation(self) -> None:
        mermaid_text = self.builder.to_mermaid(self.memories, self.synapses)
        self.assertTrue(mermaid_text.startswith("flowchart TD"))
        self.assertIn("subgraph_architecture", mermaid_text)
        self.assertIn("subgraph_debug", mermaid_text)
        self.assertIn("classDef memoryNode", mermaid_text)

    def test_json_adjacency_graph(self) -> None:
        graph = self.builder.build_adjacency_graph(self.memories, self.synapses)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertIn("clusters", graph)
        self.assertIn("metrics", graph)
        self.assertGreater(graph["metrics"]["total_nodes"], 0)
        self.assertGreater(graph["metrics"]["total_edges"], 0)

    def test_associative_pathway_dijkstra(self) -> None:
        graph = self.builder.build_adjacency_graph(self.memories, self.synapses)
        path = self.builder.find_associative_path(graph, "tag_synapse", "tag_cognitive")
        self.assertIsNotNone(path)
        self.assertGreater(len(path), 0)

    def test_sanitize_and_escape(self) -> None:
        clean_id = sanitize_mermaid_id("bad-id with spaces & symbols!")
        self.assertTrue(re.match(r"^[a-zA-Z0-9_]+$", clean_id))

        escaped_label = escape_mermaid_label('Label with "quotes" and [brackets]')
        self.assertNotIn('"', escaped_label)
        self.assertIn("#quot;", escaped_label)


if __name__ == "__main__":
    unittest.main()
