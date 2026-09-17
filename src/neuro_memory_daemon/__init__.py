"""
neuro_memory_daemon
~~~~~~~~~~~~~~~~~~~
Neuro-Cognitive Associative Memory Daemon for AI Agents & MCP Substrates.
Pure Python standard library implementation.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import uuid
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

__version__ = "0.1.0"
__author__ = "Neuro-Memory Protocol Architect"
__all__ = [
    "__version__",
    "MemoryDaemon",
    "MemoryNode",
    "store_memory",
    "recall_memory",
    "search_memories",
    "get_memory_graph",
    "consolidate_memories",
    "get_default_daemon",
    "SemanticSchemaCluster",
    "SleepReplayReport",
    "run_sleep_replay_consolidation",
    "SourceProvenance",
    "DialecticConflict",
    "MetacognitiveAuditResult",
    "MetacognitiveEvaluator",
    "audit_metacognition",
    "audit_metacognitive_memory",
]

# Optional re-exports from core sleep_replay and metacognition
try:
    from .sleep_replay import (
        SemanticSchemaCluster,
        SleepReplayReport,
        run_sleep_replay_consolidation,
    )
except ImportError:
    pass

try:
    from .metacognition import (
        SourceProvenance,
        DialecticConflict,
        MetacognitiveAuditResult,
        MetacognitiveEvaluator,
        audit_metacognition,
    )
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class MemoryNode:
    """Represents a discrete memory unit in the neural associative substrate."""
    id: str
    text: str
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5
    category: str = "episodic"  # episodic, semantic, procedural, working
    perspective: str = "first_person"  # first_person, third_person, agent, user, system
    agent_id: str = "default"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_accessed_at: float = field(default_factory=time.time)
    access_count: int = 1
    synapses: Dict[str, float] = field(default_factory=dict)  # target_id -> synaptic_weight (0.0 - 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Dict[str, float] = field(default_factory=dict)  # token -> tf-idf / frequency weight

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryNode":
        data_copy = dict(data)
        # Ensure default fields exist if loading from partial dict
        data_copy.setdefault("tags", [])
        data_copy.setdefault("importance", 0.5)
        data_copy.setdefault("category", "episodic")
        data_copy.setdefault("perspective", "first_person")
        data_copy.setdefault("agent_id", "default")
        data_copy.setdefault("created_at", time.time())
        data_copy.setdefault("updated_at", time.time())
        data_copy.setdefault("last_accessed_at", time.time())
        data_copy.setdefault("access_count", 1)
        data_copy.setdefault("synapses", {})
        data_copy.setdefault("metadata", {})
        data_copy.setdefault("embedding", {})
        return cls(**data_copy)


# ---------------------------------------------------------------------------
# Pure Python Text & Vector Utilities (Zero external dependencies)
# ---------------------------------------------------------------------------

_STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into meaningful term tokens."""
    cleaned = re.sub(r"[^\w\s\-]", " ", text.lower())
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
    return tokens

def _compute_bow_vector(text: str, tags: Optional[List[str]] = None) -> Dict[str, float]:
    """Compute normalized Term Frequency vector with tag boosting."""
    tokens = _tokenize(text)
    if tags:
        for t in tags:
            tag_tokens = _tokenize(t)
            tokens.extend(tag_tokens * 3)  # Tag boosting
    
    if not tokens:
        return {}
    
    tf: Dict[str, float] = {}
    for tok in tokens:
        if tok not in _STOP_WORDS:
            tf[tok] = tf.get(tok, 0.0) + 1.0

    # L2 normalize
    norm_sq = sum(v * v for v in tf.values())
    if norm_sq > 0:
        norm = math.sqrt(norm_sq)
        return {k: v / norm for k, v in tf.items()}
    return tf

def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Calculate cosine similarity between two sparse term vectors."""
    if not vec1 or not vec2:
        return 0.0
    common_keys = set(vec1.keys()) & set(vec2.keys())
    if not common_keys:
        return 0.0
    dot_product = sum(vec1[k] * vec2[k] for k in common_keys)
    return max(0.0, min(1.0, dot_product))


# ---------------------------------------------------------------------------
# Default Memory Daemon Substrate Engine
# ---------------------------------------------------------------------------

class MemoryDaemon:
    """
    Core Neuro-Cognitive Memory Substrate Daemon.
    Supports episodic/semantic memory, associative spreading activation recall,
    STDP synaptic plasticity, sleep consolidation, and graph exports.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None, auto_save: bool = True):
        if db_path is None:
            default_dir = Path.home() / ".neuro_memory"
            self.db_path = default_dir / "substrate.json"
        else:
            self.db_path = Path(db_path)
            
        self.auto_save = auto_save
        self._lock = threading.RLock()
        self.nodes: Dict[str, MemoryNode] = {}
        self.start_time = time.time()
        self._load()

    def _load(self) -> None:
        """Load memory substrate from persistent storage."""
        with self._lock:
            if not self.db_path.exists():
                return
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                nodes_data = data.get("nodes", {})
                self.nodes = {
                    node_id: MemoryNode.from_dict(node_dict)
                    for node_id, node_dict in nodes_data.items()
                }
            except Exception as e:
                # Log to stderr and start fresh or keep existing
                sys.stderr.write(f"[neuro-memory-daemon] Warning loading {self.db_path}: {e}\n")

    def _save(self) -> None:
        """Atomically persist memory substrate to disk."""
        if not self.auto_save:
            return
        with self._lock:
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = self.db_path.with_suffix(f".tmp.{os.getpid()}.{time.time_ns()}")
                data = {
                    "version": __version__,
                    "updated_at": time.time(),
                    "node_count": len(self.nodes),
                    "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()}
                }
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                temp_path.replace(self.db_path)
            except Exception as e:
                sys.stderr.write(f"[neuro-memory-daemon] Error saving {self.db_path}: {e}\n")

    # -----------------------------------------------------------------------
    # Public API: Store
    # -----------------------------------------------------------------------

    def store(
        self,
        text: str,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        category: str = "episodic",
        perspective: str = "first_person",
        agent_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store an episodic, semantic, procedural, or working memory into the substrate.
        Automatically computes term embedding and establishes initial synaptic connections.
        """
        if not text or not text.strip():
            raise ValueError("Memory text cannot be empty.")

        clean_text = text.strip()
        tags_list = [t.strip().lower() for t in (tags or []) if t.strip()]
        importance_clamped = max(0.0, min(1.0, float(importance)))
        meta = metadata or {}

        node_id = str(uuid.uuid4())
        embedding = _compute_bow_vector(clean_text, tags_list)

        with self._lock:
            # Form initial synaptic connections based on associative similarity & recent temporal context
            synapses: Dict[str, float] = {}
            for other_id, other_node in self.nodes.items():
                sim = _cosine_similarity(embedding, other_node.embedding)
                
                # Tag intersection bonus
                shared_tags = set(tags_list) & set(other_node.tags)
                if shared_tags:
                    sim += 0.15 * len(shared_tags)
                sim = min(1.0, sim)

                if sim >= 0.20:
                    synapses[other_id] = round(sim, 4)
                    # Bidirectional initial association with slight attenuation
                    other_node.synapses[node_id] = round(sim * 0.9, 4)

            new_node = MemoryNode(
                id=node_id,
                text=clean_text,
                tags=tags_list,
                importance=importance_clamped,
                category=category,
                perspective=perspective,
                agent_id=agent_id,
                created_at=time.time(),
                updated_at=time.time(),
                last_accessed_at=time.time(),
                access_count=1,
                synapses=synapses,
                metadata=meta,
                embedding=embedding,
            )

            self.nodes[node_id] = new_node
            self._save()

            return {
                "id": node_id,
                "text": clean_text,
                "tags": tags_list,
                "importance": importance_clamped,
                "category": category,
                "perspective": perspective,
                "agent_id": agent_id,
                "synaptic_links_formed": len(synapses),
                "created_at": new_node.created_at,
            }

    def store_memory(self, *args, **kwargs) -> Dict[str, Any]:
        """Alias for store()."""
        return self.store(*args, **kwargs)

    # -----------------------------------------------------------------------
    # Public API: Recall (Associative Pattern Completion)
    # -----------------------------------------------------------------------

    def recall(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.1,
        category: Optional[str] = None,
        spread_hops: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Perform pattern completion associative recall for a query cue.
        Traverses synaptic connections to retrieve associated memory nodes based on
        semantic similarity and graph spreading activation.
        """
        if not query or not query.strip():
            return []

        query_vec = _compute_bow_vector(query)
        if not query_vec:
            return []

        with self._lock:
            if not self.nodes:
                return []

            # 1. Direct associative resonance
            activation_scores: Dict[str, float] = {}
            for node_id, node in self.nodes.items():
                if category and node.category != category:
                    continue

                sim = _cosine_similarity(query_vec, node.embedding)
                
                # Tag cue match boost
                query_tokens = set(_tokenize(query))
                matching_tags = query_tokens & set(node.tags)
                if matching_tags:
                    sim += 0.25 * len(matching_tags)

                # Importance weighting factor
                score = (sim * 0.7) + (node.importance * 0.3)
                activation_scores[node_id] = min(1.0, score)

            # 2. Spreading activation across synapses
            current_energy = dict(activation_scores)
            for hop in range(1, spread_hops + 1):
                decay = 0.5 ** hop
                next_energy: Dict[str, float] = {}
                for source_id, energy in current_energy.items():
                    if energy < min_score:
                        continue
                    source_node = self.nodes.get(source_id)
                    if not source_node:
                        continue
                    for target_id, weight in source_node.synapses.items():
                        if target_id not in self.nodes:
                            continue
                        spread_val = energy * weight * decay
                        next_energy[target_id] = next_energy.get(target_id, 0.0) + spread_val

                # Merge spread energy
                for tid, s_val in next_energy.items():
                    activation_scores[tid] = min(1.0, activation_scores.get(tid, 0.0) + s_val)

            # 3. Filter, rank and Hebbian activity update
            ranked_ids = sorted(
                [nid for nid, s in activation_scores.items() if s >= min_score],
                key=lambda x: activation_scores[x],
                reverse=True,
            )[:top_k]

            results = []
            now = time.time()
            for nid in ranked_ids:
                node = self.nodes[nid]
                node.last_accessed_at = now
                node.access_count += 1
                
                # Strengthen synapses among co-activated results (Hebbian plasticity)
                for other_nid in ranked_ids:
                    if other_nid != nid:
                        current_w = node.synapses.get(other_nid, 0.1)
                        node.synapses[other_nid] = round(min(1.0, current_w + 0.02), 4)

                results.append({
                    "id": node.id,
                    "text": node.text,
                    "score": round(activation_scores[nid], 4),
                    "tags": node.tags,
                    "category": node.category,
                    "importance": node.importance,
                    "perspective": node.perspective,
                    "agent_id": node.agent_id,
                    "access_count": node.access_count,
                    "last_accessed_at": node.last_accessed_at,
                    "connected_synapses": len(node.synapses),
                })

            if results:
                self._save()

            return results

    def recall_memory(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Alias for recall()."""
        return self.recall(*args, **kwargs)

    # -----------------------------------------------------------------------
    # Public API: Search (Full-Text & Tag Filtering)
    # -----------------------------------------------------------------------

    def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        limit: int = 10,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform filtered search across all stored memories with token relevance ranking.
        """
        with self._lock:
            if not self.nodes:
                return []

            query_tokens = set(_tokenize(query or ""))
            filter_tags = [t.strip().lower() for t in (tags or []) if t.strip()]

            scored_nodes = []
            for node in self.nodes.values():
                if category and node.category != category:
                    continue
                if agent_id and node.agent_id != agent_id:
                    continue
                if filter_tags and not set(filter_tags).issubset(set(node.tags)):
                    continue

                score = 0.0
                node_tokens = set(_tokenize(node.text))
                if query_tokens:
                    intersect = query_tokens & node_tokens
                    if not intersect and not (set(query_tokens) & set(node.tags)):
                        continue
                    token_overlap = len(intersect) / len(query_tokens)
                    tag_overlap = len(query_tokens & set(node.tags))
                    score = (token_overlap * 0.7) + (tag_overlap * 0.3)
                else:
                    score = node.importance

                scored_nodes.append((score, node))

            scored_nodes.sort(key=lambda x: x[0], reverse=True)
            top_matches = scored_nodes[:limit]

            return [
                {
                    "id": n.id,
                    "text": n.text,
                    "score": round(sc, 4),
                    "tags": n.tags,
                    "category": n.category,
                    "importance": n.importance,
                    "perspective": n.perspective,
                    "agent_id": n.agent_id,
                    "created_at": n.created_at,
                }
                for sc, n in top_matches
            ]

    def search_memories(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Alias for search()."""
        return self.search(*args, **kwargs)

    # -----------------------------------------------------------------------
    # Public API: Synaptic Graph
    # -----------------------------------------------------------------------

    def get_graph(
        self,
        format: str = "json",
        min_weight: float = 0.1,
        node_limit: int = 50,
        root_id: Optional[str] = None,
    ) -> Union[Dict[str, Any], str]:
        """
        Return synaptic graph relationships as JSON, Mermaid, ASCII or DOT format.
        """
        with self._lock:
            nodes_subset = list(self.nodes.values())
            if root_id and root_id in self.nodes:
                # Local ego graph around root_id
                ego_node = self.nodes[root_id]
                connected_ids = {root_id} | {
                    tid for tid, w in ego_node.synapses.items() if w >= min_weight
                }
                nodes_subset = [n for n in nodes_subset if n.id in connected_ids]
            
            nodes_subset = nodes_subset[:node_limit]
            node_ids = {n.id for n in nodes_subset}

            edges = []
            for n in nodes_subset:
                for target_id, weight in n.synapses.items():
                    if target_id in node_ids and weight >= min_weight:
                        edges.append({
                            "source": n.id,
                            "target": target_id,
                            "weight": round(weight, 3),
                        })

            if format == "json":
                return {
                    "nodes": [
                        {
                            "id": n.id,
                            "label": n.text[:40] + ("..." if len(n.text) > 40 else ""),
                            "category": n.category,
                            "importance": n.importance,
                            "tags": n.tags,
                            "access_count": n.access_count,
                        }
                        for n in nodes_subset
                    ],
                    "edges": edges,
                    "total_nodes": len(nodes_subset),
                    "total_edges": len(edges),
                }

            elif format == "mermaid":
                lines = ["graph TD"]
                # Sanitize text for Mermaid labels
                for n in nodes_subset:
                    clean_label = n.text[:30].replace('"', "'").replace("\n", " ")
                    tag_str = f" [{','.join(n.tags[:2])}]" if n.tags else ""
                    lines.append(f'    n_{n.id[:8]}["{clean_label}{tag_str}"]')
                for e in edges:
                    lines.append(f'    n_{e["source"][:8]} -->|{e["weight"]}| n_{e["target"][:8]}')
                return "\n".join(lines)

            elif format == "ascii":
                lines = [
                    f"=== Synaptic Memory Substrate ({len(nodes_subset)} nodes, {len(edges)} edges) ==="
                ]
                for n in nodes_subset:
                    lines.append(f"• [{n.category.upper()}] ({n.id[:8]}) {n.text[:60]}")
                    outgoing = [
                        f"{tid[:8]}(w={w})"
                        for tid, w in n.synapses.items()
                        if tid in node_ids and w >= min_weight
                    ]
                    if outgoing:
                        lines.append(f"   └── Synapses ➔ {', '.join(outgoing)}")
                return "\n".join(lines)

            elif format == "dot":
                lines = ["digraph MemorySubstrate {", "    rankdir=LR;", "    node [shape=box, style=rounded];"]
                for n in nodes_subset:
                    lbl = n.text[:25].replace('"', '\\"')
                    lines.append(f'    "{n.id[:8]}" [label="{lbl}"];')
                for e in edges:
                    lines.append(f'    "{e["source"][:8]}" -> "{e["target"][:8]}" [label="{e["weight"]}"];')
                lines.append("}")
                return "\n".join(lines)

            else:
                raise ValueError(f"Unsupported graph format: {format}")

    def get_memory_graph(self, *args, **kwargs) -> Union[Dict[str, Any], str]:
        """Alias for get_graph()."""
        return self.get_graph(*args, **kwargs)

    # -----------------------------------------------------------------------
    # Public API: Consolidation (Sleep & STDP Plasticity)
    # -----------------------------------------------------------------------

    def consolidate(
        self,
        decay_rate: float = 0.05,
        prune_threshold: float = 0.05,
        stdp_window: float = 3600.0,
    ) -> Dict[str, Any]:
        """
        Trigger sleep/consolidation pass:
        - Applies exponential decay to importance and synaptic weights.
        - Applies STDP (Spike-Timing-Dependent Plasticity) for co-activated nodes.
        - Prunes sub-threshold synaptic connections and ephemeral memories.
        """
        start_ts = time.time()
        with self._lock:
            nodes_processed = len(self.nodes)
            decayed_count = 0
            pruned_synapses = 0
            strengthened_synapses = 0
            pruned_nodes = 0

            now = time.time()
            nodes_to_delete: List[str] = []

            for node_id, node in list(self.nodes.items()):
                # Elapsed days since last access
                elapsed_days = max(0.0, (now - node.last_accessed_at) / 86400.0)
                
                # Ebbinghaus-style repetition resistance: more accesses = slower decay
                resistance = 1.0 + math.log1p(node.access_count)
                effective_decay = (decay_rate * elapsed_days) / resistance

                # Decay importance
                old_imp = node.importance
                node.importance = max(0.01, node.importance * (1.0 - effective_decay))
                if old_imp != node.importance:
                    decayed_count += 1

                # Synaptic STDP and decay
                synapses_to_remove = []
                for target_id, weight in list(node.synapses.items()):
                    if target_id not in self.nodes:
                        synapses_to_remove.append(target_id)
                        continue

                    target_node = self.nodes[target_id]
                    time_diff = target_node.last_accessed_at - node.last_accessed_at

                    # STDP rule: if target was activated shortly after node (causal sequence)
                    if 0 < time_diff <= stdp_window:
                        # Potentiation (LTP)
                        weight = min(1.0, weight + 0.05)
                        strengthened_synapses += 1
                    elif 0 < -time_diff <= stdp_window:
                        # Depression (LTD)
                        weight = max(0.0, weight - 0.03)

                    # General weight decay
                    weight = weight * (1.0 - effective_decay)

                    if weight < prune_threshold:
                        synapses_to_remove.append(target_id)
                        pruned_synapses += 1
                    else:
                        node.synapses[target_id] = round(weight, 4)

                for tid in synapses_to_remove:
                    node.synapses.pop(tid, None)

                # Pruning working memories that decayed below threshold
                if node.category == "working" and node.importance < prune_threshold and node.access_count <= 1:
                    nodes_to_delete.append(node_id)

            for nid in nodes_to_delete:
                self.nodes.pop(nid, None)
                pruned_nodes += 1
                # Clean up dangling references
                for remaining_node in self.nodes.values():
                    remaining_node.synapses.pop(nid, None)

            self._save()
            duration = round(time.time() - start_ts, 4)

            return {
                "nodes_processed": nodes_processed,
                "decayed_nodes": decayed_count,
                "strengthened_synapses": strengthened_synapses,
                "pruned_synapses": pruned_synapses,
                "pruned_nodes": pruned_nodes,
                "remaining_nodes": len(self.nodes),
                "duration_seconds": duration,
            }

    def consolidate_memories(self, *args, **kwargs) -> Dict[str, Any]:
        """Alias for consolidate()."""
        return self.consolidate(*args, **kwargs)

    def audit_metacognition(
        self,
        query: str = "",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Perform metacognitive evaluation: Feeling-of-Knowing (FOK), Tip-of-the-Tongue, and ACC conflict detection."""
        from .metacognition import audit_metacognition as _audit
        return _audit(self, query=query, top_k=top_k)

    # -----------------------------------------------------------------------
    # Public API: Stats & Diagnostics
    # -----------------------------------------------------------------------

    def get_stats(self, detailed: bool = False) -> Dict[str, Any]:
        """Return memory substrate metrics and telemetry."""
        with self._lock:
            total_memories = len(self.nodes)
            total_synapses = sum(len(n.synapses) for n in self.nodes.values())
            
            categories: Dict[str, int] = {}
            tags_count: Dict[str, int] = {}
            avg_importance = 0.0
            avg_accesses = 0.0

            if total_memories > 0:
                imp_sum = 0.0
                acc_sum = 0
                for n in self.nodes.values():
                    categories[n.category] = categories.get(n.category, 0) + 1
                    for t in n.tags:
                        tags_count[t] = tags_count.get(t, 0) + 1
                    imp_sum += n.importance
                    acc_sum += n.access_count
                avg_importance = round(imp_sum / total_memories, 3)
                avg_accesses = round(acc_sum / total_memories, 2)

            synaptic_density = (
                round(total_synapses / total_memories, 2) if total_memories > 0 else 0.0
            )

            stats = {
                "total_memories": total_memories,
                "total_synapses": total_synapses,
                "synaptic_density": synaptic_density,
                "working_memory_usage": categories.get("working", 0),
                "average_importance": avg_importance,
                "average_accesses": avg_accesses,
                "categories": categories,
            }

            if detailed:
                top_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:15]
                stats["top_tags"] = dict(top_tags)
                stats["storage_path"] = str(self.db_path)
                stats["file_size_bytes"] = (
                    self.db_path.stat().st_size if self.db_path.exists() else 0
                )

            return stats

    def diagnostics(self, verbose: bool = False) -> Dict[str, Any]:
        """System health and diagnostic inspection report."""
        import platform
        with self._lock:
            db_exists = self.db_path.exists()
            file_size = self.db_path.stat().st_size if db_exists else 0
            uptime = round(time.time() - self.start_time, 2)

            diag = {
                "status": "healthy",
                "version": __version__,
                "uptime_seconds": uptime,
                "db_path": str(self.db_path),
                "db_exists": db_exists,
                "db_size_bytes": file_size,
                "nodes_count": len(self.nodes),
                "python_version": platform.python_version(),
                "system": platform.system(),
                "machine": platform.machine(),
            }

            if verbose:
                diag["node_categories"] = {
                    cat: sum(1 for n in self.nodes.values() if n.category == cat)
                    for cat in ["episodic", "semantic", "procedural", "working"]
                }
                diag["synapse_weights_distribution"] = {
                    "strong (>0.7)": sum(
                        1
                        for n in self.nodes.values()
                        for w in n.synapses.values()
                        if w > 0.7
                    ),
                    "moderate (0.3-0.7)": sum(
                        1
                        for n in self.nodes.values()
                        for w in n.synapses.values()
                        if 0.3 <= w <= 0.7
                    ),
                    "weak (<0.3)": sum(
                        1
                        for n in self.nodes.values()
                        for w in n.synapses.values()
                        if w < 0.3
                    ),
                }

            return diag


# ---------------------------------------------------------------------------
# Global Singleton & Convenience Functional API
# ---------------------------------------------------------------------------

_GLOBAL_DAEMON: Optional[MemoryDaemon] = None
_GLOBAL_LOCK = threading.RLock()

def get_default_daemon(db_path: Optional[Union[str, Path]] = None) -> MemoryDaemon:
    """Retrieve or initialize the global singleton MemoryDaemon instance."""
    global _GLOBAL_DAEMON
    with _GLOBAL_LOCK:
        if _GLOBAL_DAEMON is None or (db_path and Path(db_path) != _GLOBAL_DAEMON.db_path):
            _GLOBAL_DAEMON = MemoryDaemon(db_path=db_path)
        return _GLOBAL_DAEMON

def store_memory(
    text: str,
    tags: Optional[List[str]] = None,
    importance: float = 0.5,
    category: str = "episodic",
    perspective: str = "first_person",
    agent_id: str = "default",
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Store memory using the default daemon substrate."""
    daemon = get_default_daemon(db_path)
    return daemon.store(
        text=text,
        tags=tags,
        importance=importance,
        category=category,
        perspective=perspective,
        agent_id=agent_id,
        metadata=metadata,
    )

def recall_memory(
    query: str,
    top_k: int = 5,
    min_score: float = 0.1,
    category: Optional[str] = None,
    spread_hops: int = 2,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Recall memories associative to query cue using the default daemon substrate."""
    daemon = get_default_daemon(db_path)
    return daemon.recall(
        query=query,
        top_k=top_k,
        min_score=min_score,
        category=category,
        spread_hops=spread_hops,
    )

def search_memories(
    query: str,
    tags: Optional[List[str]] = None,
    category: Optional[str] = None,
    limit: int = 10,
    agent_id: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Search stored memories using the default daemon substrate."""
    daemon = get_default_daemon(db_path)
    return daemon.search(
        query=query,
        tags=tags,
        category=category,
        limit=limit,
        agent_id=agent_id,
    )

def get_memory_graph(
    format: str = "json",
    min_weight: float = 0.1,
    node_limit: int = 50,
    root_id: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> Union[Dict[str, Any], str]:
    """Retrieve synaptic graph representation using the default daemon substrate."""
    daemon = get_default_daemon(db_path)
    return daemon.get_graph(
        format=format,
        min_weight=min_weight,
        node_limit=node_limit,
        root_id=root_id,
    )

def consolidate_memories(
    decay_rate: float = 0.05,
    prune_threshold: float = 0.05,
    stdp_window: float = 3600.0,
    db_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Trigger memory consolidation pass using the default daemon substrate."""
    daemon = get_default_daemon(db_path)
    return daemon.consolidate(
        decay_rate=decay_rate,
        prune_threshold=prune_threshold,
        stdp_window=stdp_window,
    )

def audit_metacognitive_memory(
    query: str = "",
    top_k: int = 5,
    db_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Audit metacognitive Feeling-of-Knowing and detect contradictions using default daemon."""
    daemon = get_default_daemon(db_path)
    return daemon.audit_metacognition(query=query, top_k=top_k)
