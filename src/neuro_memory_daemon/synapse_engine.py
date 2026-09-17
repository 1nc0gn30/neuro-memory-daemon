"""Neuroscience-inspired cognitive algorithms and synaptic retrieval engine.

Implements:
1. Spike-Timing-Dependent Plasticity (STDP) for associative tag/entity reinforcement.
2. Hippocampal Pattern Completion & Separation (CA3 recurrent auto-associative network
   and Dentate Gyrus/CA1 orthogonalization).
3. Dorsolateral Prefrontal Cortex (DLPFC) Working Memory buffer (configurable LRU).
4. Ebbinghaus Forgetting Curve & Systems Memory Consolidation.
5. Pure-Python TF-IDF sparse vector cosine similarity ranking.
Zero external dependencies (pure Python standard library).
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from neuro_memory_daemon.storage import MemoryRecord, StorageEngine, SynapseRecord, normalize_tags

# Standard English stop words for lightweight TF-IDF indexing
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves",
}


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words, splitting camelCase and snake_case.

    Args:
        text: Input string.

    Returns:
        List of cleaned, non-stopword tokens.
    """
    if not text:
        return []

    # Split camelCase words: "neuroMemory" -> "neuro Memory"
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    # Replace non-alphanumeric characters with spaces
    s2 = re.sub(r"[^\w\s]", " ", s1)
    # Extract words
    raw_tokens = s2.lower().split()

    tokens: List[str] = []
    for token in raw_tokens:
        # Strip underscores
        t = token.strip("_")
        if len(t) > 1 and t not in STOP_WORDS and not t.isdigit():
            tokens.append(t)
    return tokens


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Compute sublinear Term Frequency (TF) for a token list.

    tf(t, d) = 1 + log(count(t, d))
    """
    if not tokens:
        return {}
    counts = Counter(tokens)
    tf_dict: Dict[str, float] = {}
    for term, count in counts.items():
        tf_dict[term] = 1.0 + math.log(count)
    return tf_dict


def compute_sparse_cosine_similarity(
    vec1: Dict[str, float],
    vec2: Dict[str, float],
) -> float:
    """Compute cosine similarity between two sparse vector dictionaries."""
    if not vec1 or not vec2:
        return 0.0

    # Determine smaller vector to iterate over
    if len(vec1) > len(vec2):
        vec1, vec2 = vec2, vec1

    dot_product = sum(weight * vec2[term] for term, weight in vec1.items() if term in vec2)
    if dot_product <= 0.0:
        return 0.0

    norm1 = math.sqrt(sum(w * w for w in vec1.values()))
    norm2 = math.sqrt(sum(w * w for w in vec2.values()))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return min(1.0, max(0.0, dot_product / (norm1 * norm2)))


@dataclass
class RecallResult:
    """Detailed cognitive recall result record.

    Attributes:
        memory: The recalled MemoryRecord.
        score: Unified cognitive ranking score (0.0 to 1.0+).
        similarity_score: Cosine TF-IDF semantic match score.
        retention_score: Ebbinghaus retention probability (0.0 to 1.0).
        synaptic_score: Associative STDP activation score.
        working_memory_boost: Working memory priming multiplier.
        association_path: Chain of associative cues linking query to memory.
    """

    memory: MemoryRecord
    score: float
    similarity_score: float = 0.0
    retention_score: float = 1.0
    synaptic_score: float = 0.0
    working_memory_boost: float = 0.0
    association_path: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "id": self.memory.id,
            "text": self.memory.text,
            "category": self.memory.category,
            "tags": self.memory.tags,
            "importance": self.memory.importance,
            "score": round(self.score, 4),
            "similarity_score": round(self.similarity_score, 4),
            "retention_score": round(self.retention_score, 4),
            "synaptic_score": round(self.synaptic_score, 4),
            "working_memory_boost": round(self.working_memory_boost, 4),
            "association_path": self.association_path,
        }


class DLPFCWorkingMemory:
    """Dorsolateral Prefrontal Cortex (DLPFC) Working Memory Buffer.

    Maintains an active, bounded cognitive scratchpad with LRU eviction,
    priority retention, and contextual priming. Default capacity is Miller's Law (7 items).
    """

    def __init__(self, capacity: int = 7) -> None:
        """Initialize working memory buffer.

        Args:
            capacity: Maximum number of active memory traces to retain in buffer.
        """
        self.capacity = max(1, capacity)
        self._buffer: OrderedDict[str, MemoryRecord] = OrderedDict()
        self._active_timestamps: Dict[str, float] = {}

    def put(self, memory: MemoryRecord) -> Optional[MemoryRecord]:
        """Insert or refresh a memory trace in active working memory.

        Args:
            memory: MemoryRecord to activate in working memory.

        Returns:
            Evicted MemoryRecord if capacity was exceeded, or None.
        """
        evicted: Optional[MemoryRecord] = None
        mem_id = memory.id

        if mem_id in self._buffer:
            self._buffer.move_to_end(mem_id)
            self._buffer[mem_id] = memory
            self._active_timestamps[mem_id] = time.time()
            return None

        # If at capacity, evict the oldest least-important item
        if len(self._buffer) >= self.capacity:
            evicted_id, evicted_mem = self._buffer.popitem(last=False)
            self._active_timestamps.pop(evicted_id, None)
            evicted = evicted_mem

        self._buffer[mem_id] = memory
        self._active_timestamps[mem_id] = time.time()
        return evicted

    def get(self, memory_id: str) -> Optional[MemoryRecord]:
        """Retrieve a memory trace from working memory, refreshing its LRU position."""
        if memory_id in self._buffer:
            self._buffer.move_to_end(memory_id)
            self._active_timestamps[memory_id] = time.time()
            return self._buffer[memory_id]
        return None

    def contains(self, memory_id: str) -> bool:
        """Check if memory ID resides in active working memory."""
        return memory_id in self._buffer

    def get_active_memories(self) -> List[MemoryRecord]:
        """Return list of active memories ordered from most recent to oldest."""
        return list(reversed(list(self._buffer.values())))

    def get_active_tags(self) -> Set[str]:
        """Return set of all tags present in active working memory."""
        tags: Set[str] = set()
        for mem in self._buffer.values():
            tags.update(mem.tags)
        return tags

    def clear(self) -> None:
        """Flush working memory buffer."""
        self._buffer.clear()
        self._active_timestamps.clear()

    @property
    def size(self) -> int:
        """Current number of active working memory traces."""
        return len(self._buffer)


class SynapseEngine:
    """Neuroscience-inspired cognitive synaptic engine.

    Orchestrates STDP synaptic plasticity, CA3/CA1 pattern completion/separation,
    Ebbinghaus decay consolidation, and TF-IDF associative recall.
    """

    def __init__(
        self,
        storage: StorageEngine,
        working_memory_capacity: int = 7,
        base_half_life_seconds: float = 86400.0,
        stdp_a_plus: float = 0.25,
        stdp_tau_plus: float = 60.0,
    ) -> None:
        """Initialize the Synapse Engine.

        Args:
            storage: Underlying StorageEngine instance.
            working_memory_capacity: Working memory buffer capacity (DLPFC).
            base_half_life_seconds: Ebbinghaus baseline half-life in seconds (default: 24h).
            stdp_a_plus: STDP potentiation scaling constant (LTP amplitude).
            stdp_tau_plus: STDP temporal plasticity window in seconds.
        """
        self.storage = storage
        self.working_memory = DLPFCWorkingMemory(capacity=working_memory_capacity)
        self.base_half_life = base_half_life_seconds
        self.a_plus = stdp_a_plus
        self.tau_plus = stdp_tau_plus

    # -------------------------------------------------------------------------
    # 1. Spike-Timing-Dependent Plasticity (STDP)
    # -------------------------------------------------------------------------

    def reinforce_synapse(
        self,
        node_a: str,
        node_b: str,
        delta_t: float = 0.0,
        synapse_type: str = "tag_tag",
        timestamp: Optional[float] = None,
    ) -> float:
        """Reinforce the synaptic connection between node_a and node_b via STDP.

        Hebbian Long-Term Potentiation (LTP):
        delta_w = A_+ * exp(-|delta_t| / tau_+)
        w_new = min(1.0, w_old + delta_w * (1 - w_old))

        Args:
            node_a: First entity tag or ID.
            node_b: Second entity tag or ID.
            delta_t: Time difference between activation spikes (in seconds).
            synapse_type: Synapse category ('tag_tag', 'memory_memory', etc.).
            timestamp: Activation timestamp.

        Returns:
            Updated synaptic weight (0.0 to 1.0).
        """
        if node_a == node_b:
            return 1.0

        ts = timestamp if timestamp is not None else time.time()
        existing = self.storage.get_synapse(node_a, node_b, synapse_type=synapse_type)
        current_weight = existing.weight if existing else 0.05
        co_occur = existing.co_occurrence_count + 1 if existing else 1

        # STDP potentiation calculation
        dt = abs(delta_t)
        dw = self.a_plus * math.exp(-dt / self.tau_plus)
        # Asymptotic soft-saturation towards 1.0
        new_weight = min(1.0, current_weight + dw * (1.0 - current_weight))

        # Update bi-directional connection
        self.storage.save_synapse(
            source=node_a,
            target=node_b,
            weight=new_weight,
            synapse_type=synapse_type,
            timestamp=ts,
            co_occur_delta=1,
        )
        self.storage.save_synapse(
            source=node_b,
            target=node_a,
            weight=new_weight,
            synapse_type=synapse_type,
            timestamp=ts,
            co_occur_delta=1,
        )

        return new_weight

    def record_coactivation(
        self,
        nodes: List[str],
        timestamp: Optional[float] = None,
        synapse_type: str = "tag_tag",
    ) -> None:
        """Record co-activation / synchronous firing across a cluster of nodes.

        Reinforces all pairwise synapses between activated nodes.

        Args:
            nodes: List of co-activated tags or entity IDs.
            timestamp: Activation timestamp.
            synapse_type: Synapse classification.
        """
        cleaned_nodes = list(set(normalize_tags(nodes)))
        if len(cleaned_nodes) < 2:
            return

        ts = timestamp if timestamp is not None else time.time()
        for i in range(len(cleaned_nodes)):
            for j in range(i + 1, len(cleaned_nodes)):
                self.reinforce_synapse(
                    node_a=cleaned_nodes[i],
                    node_b=cleaned_nodes[j],
                    delta_t=0.0,
                    synapse_type=synapse_type,
                    timestamp=ts,
                )

    def get_associated_nodes(
        self,
        node: str,
        min_weight: float = 0.05,
        max_depth: int = 2,
    ) -> List[Tuple[str, float]]:
        """Find nodes associatively connected to the given node via synaptic pathways.

        Performs a spreading activation search up to max_depth hops.

        Args:
            node: Origin node tag.
            min_weight: Minimum weight threshold for inclusion.
            max_depth: Maximum associative graph search depth.

        Returns:
            List of (associated_node, cumulative_activation_weight) sorted descending.
        """
        start = node.strip().lower()
        visited: Dict[str, float] = {start: 1.0}
        frontier: List[Tuple[str, float, int]] = [(start, 1.0, 0)]

        while frontier:
            curr_node, curr_act, depth = frontier.pop(0)
            if depth >= max_depth:
                continue

            synapses = self.storage.get_synapses_for_node(curr_node, min_weight=min_weight)
            for syn in synapses:
                neighbor = syn.target if syn.source == curr_node else syn.source
                if neighbor == start:
                    continue

                attenuation = 0.7  # Hop attenuation factor
                neighbor_act = curr_act * syn.weight * attenuation
                if neighbor_act >= min_weight:
                    if neighbor not in visited or neighbor_act > visited[neighbor]:
                        visited[neighbor] = neighbor_act
                        frontier.append((neighbor, neighbor_act, depth + 1))

        results = [(k, round(v, 4)) for k, v in visited.items() if k != start]
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def decay_synapses(
        self,
        current_time: Optional[float] = None,
        half_life_seconds: Optional[float] = None,
    ) -> int:
        """Apply passive exponential decay to all synapses and prune dead connections.

        Args:
            current_time: Current timestamp.
            half_life_seconds: Decay half life in seconds.

        Returns:
            Number of pruned dead synapses.
        """
        hl = half_life_seconds if half_life_seconds is not None else self.base_half_life * 7.0
        decay_rate = math.log(2) / hl
        # Decay all
        self.storage.decay_all_synapses(decay_rate, 3600.0)
        # Prune dead synapses
        return self.storage.prune_synapses(min_weight=0.02)

    # -------------------------------------------------------------------------
    # 2. Hippocampal Pattern Completion & Separation (CA3/CA1)
    # -------------------------------------------------------------------------

    def pattern_completion(
        self,
        query_cues: List[str],
        max_expansions: int = 6,
        min_synapse_weight: float = 0.12,
    ) -> Dict[str, Any]:
        """CA3 Recurrent Auto-Associative Pattern Completion.

        Reconstructs a full associative memory context from a partial or degraded query cue.
        Traverses synaptic pathways to infer associated concepts, missing tags, and related entities.

        Args:
            query_cues: List of initial cue tokens or tags.
            max_expansions: Maximum number of associative tags to append.
            min_synapse_weight: Minimum synaptic connection strength to traverse.

        Returns:
            Dictionary containing:
                - original_cues: Initial input tags/tokens.
                - completed_tags: Expanded associative tags.
                - activation_scores: Mapping of tag to synaptic activation strength.
                - completion_confidence: Confidence score of pattern completion.
        """
        normalized_cues = normalize_tags(query_cues)
        if not normalized_cues:
            return {
                "original_cues": [],
                "completed_tags": [],
                "activation_scores": {},
                "completion_confidence": 0.0,
            }

        activation_map: Dict[str, float] = defaultdict(float)
        for cue in normalized_cues:
            activation_map[cue] += 1.0
            associations = self.get_associated_nodes(cue, min_weight=min_synapse_weight, max_depth=2)
            for assoc_tag, weight in associations:
                activation_map[assoc_tag] += weight

        # Sort expanded tags by activation energy
        sorted_activations = sorted(
            [(tag, score) for tag, score in activation_map.items() if tag not in normalized_cues],
            key=lambda x: x[1],
            reverse=True,
        )

        completed_tags = [tag for tag, _ in sorted_activations[:max_expansions]]
        total_energy = sum(score for _, score in sorted_activations[:max_expansions])
        confidence = min(1.0, total_energy / (len(normalized_cues) + 1.0))

        return {
            "original_cues": normalized_cues,
            "completed_tags": completed_tags,
            "activation_scores": {k: round(v, 4) for k, v in activation_map.items()},
            "completion_confidence": round(confidence, 4),
        }

    def pattern_separation(
        self,
        new_text: str,
        candidate_tags: List[str],
        candidate_pool: Optional[List[MemoryRecord]] = None,
    ) -> Tuple[float, List[str]]:
        """Dentate Gyrus / CA1 Pattern Separation (Orthogonalization).

        Prevents catastrophic interference by distinguishing similar but distinct
        memory traces and identifying unique orthogonal features.

        Args:
            new_text: Content of candidate new memory trace.
            candidate_tags: Proposed tags for the new memory.
            candidate_pool: Optional pool of existing memories to compare against.

        Returns:
            Tuple of (distinctiveness_score, disambiguating_tags):
                - distinctiveness_score: 1.0 (completely distinct) to 0.0 (exact duplicate).
                - disambiguating_tags: Specific unique tokens/tags to prevent collision.
        """
        new_tokens = set(tokenize(new_text))
        if not new_tokens:
            return 1.0, candidate_tags

        pool = candidate_pool if candidate_pool is not None else self.storage.list_memories(limit=100)
        if not pool:
            return 1.0, candidate_tags

        max_overlap = 0.0
        overlapping_memory: Optional[MemoryRecord] = None

        for existing in pool:
            existing_tokens = set(tokenize(existing.text))
            if not existing_tokens:
                continue
            intersection = new_tokens.intersection(existing_tokens)
            union = new_tokens.union(existing_tokens)
            jaccard = len(intersection) / len(union) if union else 0.0

            if jaccard > max_overlap:
                max_overlap = jaccard
                overlapping_memory = existing

        distinctiveness_score = round(1.0 - max_overlap, 4)

        # Extract orthogonal residual tokens (present in new memory, absent in most similar existing memory)
        disambiguating_tags = list(candidate_tags)
        if max_overlap > 0.65 and overlapping_memory:
            overlap_tokens = set(tokenize(overlapping_memory.text))
            residual_tokens = [t for t in new_tokens if t not in overlap_tokens]
            # Pick top 2 most distinctive residual tokens as disambiguation tags
            for res_tok in residual_tokens[:2]:
                if res_tok not in disambiguating_tags:
                    disambiguating_tags.append(res_tok)

        return distinctiveness_score, normalize_tags(disambiguating_tags)

    # -------------------------------------------------------------------------
    # 3. Forgetting Curve & Systems Memory Consolidation (Ebbinghaus)
    # -------------------------------------------------------------------------

    def calculate_retention(
        self,
        record: MemoryRecord,
        current_time: Optional[float] = None,
    ) -> float:
        """Calculate Ebbinghaus retention probability R(t) for a memory trace.

        Formula:
        R(t) = exp(- delta_t / Strength)
        Strength = S_0 * decay_factor * (1 + ln(1 + access_count)) * (1 + importance)

        Args:
            record: MemoryRecord to evaluate.
            current_time: Current timestamp (defaults to time.time()).

        Returns:
            Retention score between 0.0 (forgotten) and 1.0 (fully retained).
        """
        if record.immutable:
            return 1.0

        ts = current_time if current_time is not None else time.time()
        delta_t = max(0.0, ts - record.last_accessed_at)

        # Calculate memory strength / stability
        access_bonus = 1.0 + math.log(1.0 + record.access_count)
        importance_bonus = 1.0 + max(0.0, record.importance)
        decay_factor = max(0.1, record.decay_factor)

        strength = self.base_half_life * decay_factor * access_bonus * importance_bonus
        retention = math.exp(-delta_t / max(1.0, strength))

        return round(min(1.0, max(0.0, retention)), 4)

    def identify_pruning_candidates(
        self,
        memories: List[MemoryRecord],
        retention_threshold: float = 0.12,
        current_time: Optional[float] = None,
    ) -> List[MemoryRecord]:
        """Identify memory traces that have degraded below the retention threshold.

        Filters out immutable memories.

        Args:
            memories: List of candidate memories.
            retention_threshold: Cutoff retention score below which memory is pruned.
            current_time: Evaluation timestamp.

        Returns:
            List of MemoryRecord objects eligible for pruning.
        """
        candidates: List[MemoryRecord] = []
        for mem in memories:
            if mem.immutable:
                continue
            retention = self.calculate_retention(mem, current_time=current_time)
            if retention < retention_threshold:
                candidates.append(mem)
        return candidates

    def consolidate_memory(self, record: MemoryRecord) -> MemoryRecord:
        """Systems Consolidation: Transform episodic trace into stable semantic memory.

        Elevates decay factor, refines categorization, and updates persistent storage.

        Args:
            record: MemoryRecord to consolidate.

        Returns:
            Consolidated MemoryRecord.
        """
        # Strengthen decay resistance
        new_decay_factor = record.decay_factor * 1.5
        new_importance = min(2.0, record.importance * 1.2)

        # Categorize promotion
        new_category = record.category
        if record.access_count >= 5 and record.category in ("general", "episodic"):
            new_category = "insight"

        updated = self.storage.update_memory(
            record.id,
            decay_factor=new_decay_factor,
            importance=new_importance,
            category=new_category,
        )
        return updated or record

    # -------------------------------------------------------------------------
    # 4. Cognitive Retrieval & Sparse TF-IDF Vector Ranking
    # -------------------------------------------------------------------------

    def _build_corpus_tfidf(
        self,
        memories: List[MemoryRecord],
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """Compute Corpus IDF and per-memory TF-IDF sparse vectors."""
        num_docs = len(memories)
        if num_docs == 0:
            return {}, {}

        doc_tfs: Dict[str, Dict[str, float]] = {}
        doc_freqs: Dict[str, int] = defaultdict(int)

        for mem in memories:
            # Combine text and tags with tag weighting
            tokens = tokenize(mem.text)
            for tag in mem.tags:
                tokens.extend(tokenize(tag) * 2)  # Tag boosting

            tf = compute_tf(tokens)
            doc_tfs[mem.id] = tf
            for term in tf.keys():
                doc_freqs[term] += 1

        # Calculate smooth IDF: idf(t) = ln((1 + N) / (1 + df)) + 1
        idfs: Dict[str, float] = {}
        for term, df in doc_freqs.items():
            idfs[term] = math.log((1.0 + num_docs) / (1.0 + df)) + 1.0

        # Compute TF-IDF sparse vectors
        memory_tfidf: Dict[str, Dict[str, float]] = {}
        for mem_id, tf in doc_tfs.items():
            vec: Dict[str, float] = {}
            for term, val in tf.items():
                vec[term] = val * idfs.get(term, 1.0)
            memory_tfidf[mem_id] = vec

        return idfs, memory_tfidf

    def recall(
        self,
        query: str,
        agent_id: Optional[str] = None,
        top_k: int = 10,
        min_score: float = 0.05,
        category: Optional[str] = None,
        auto_activate_working_memory: bool = True,
        auto_reinforce_stdp: bool = True,
    ) -> List[RecallResult]:
        """Perform unified cognitive memory recall.

        Combines:
        1. TF-IDF sparse cosine similarity.
        2. CA3 Hippocampal pattern completion (associative tag expansion).
        3. Ebbinghaus retention curve score.
        4. STDP synaptic activation energy.
        5. DLPFC working memory priming boost.

        Args:
            query: Natural language query or tag cues.
            agent_id: Optional agent ownership filter.
            top_k: Maximum number of memories to recall.
            min_score: Minimum unified score cutoff.
            category: Optional category filter.
            auto_activate_working_memory: If True, pushes top recall into DLPFC.
            auto_reinforce_stdp: If True, triggers STDP reinforcement between query & recalled tags.

        Returns:
            List of RecallResult objects sorted by cognitive score descending.
        """
        all_memories = self.storage.list_memories(
            agent_id=agent_id,
            category=category,
            limit=10000,
        )
        if not all_memories:
            return []

        # 1. Extract query tokens and tags
        query_tokens = tokenize(query)
        query_tf = compute_tf(query_tokens)

        # 2. CA3 Pattern Completion on query cues
        completion = self.pattern_completion(query_tokens, max_expansions=5)
        completed_tags = set(completion.get("completed_tags", []))
        activation_scores = completion.get("activation_scores", {})

        # 3. Build TF-IDF Corpus representation
        idfs, memory_tfidf = self._build_corpus_tfidf(all_memories)

        # Build weighted query vector (including completed tags)
        query_vec: Dict[str, float] = {}
        for term, tf_val in query_tf.items():
            query_vec[term] = tf_val * idfs.get(term, 1.0)
        for ctag in completed_tags:
            tag_toks = tokenize(ctag)
            for tt in tag_toks:
                query_vec[tt] = query_vec.get(tt, 0.0) + (activation_scores.get(ctag, 0.5) * idfs.get(tt, 1.0) * 0.5)

        results: List[RecallResult] = []
        now = time.time()

        for mem in all_memories:
            mem_vec = memory_tfidf.get(mem.id, {})
            # A. Cosine semantic similarity
            sim_score = compute_sparse_cosine_similarity(query_vec, mem_vec)

            # B. Ebbinghaus Retention Score
            ret_score = self.calculate_retention(mem, current_time=now)

            # C. Synaptic Activation Score
            synaptic_score = 0.0
            matched_tags: List[str] = []
            for tag in mem.tags:
                if tag in activation_scores:
                    synaptic_score += activation_scores[tag]
                    matched_tags.append(tag)
            normalized_synaptic = min(1.0, synaptic_score / max(1.0, len(mem.tags)))

            # D. DLPFC Working Memory Boost
            wm_boost = 0.35 if self.working_memory.contains(mem.id) else 0.0

            # E. Importance multiplier
            imp_multiplier = max(0.5, min(2.0, mem.importance))

            # F. Unified Cognitive Score Formula:
            # Score = (0.45 * Sim + 0.20 * Ret + 0.20 * Syn + 0.15 * WM) * Importance
            base_score = (
                0.45 * sim_score
                + 0.20 * ret_score
                + 0.20 * normalized_synaptic
                + 0.15 * wm_boost
            )
            final_score = base_score * imp_multiplier

            # Bonus for tag overlap
            if any(t in query_tokens for t in mem.tags):
                final_score += 0.15

            if final_score >= min_score or (sim_score > 0.2):
                results.append(
                    RecallResult(
                        memory=mem,
                        score=final_score,
                        similarity_score=sim_score,
                        retention_score=ret_score,
                        synaptic_score=normalized_synaptic,
                        working_memory_boost=wm_boost,
                        association_path=matched_tags,
                    )
                )

        # Sort descending by unified score
        results.sort(key=lambda r: r.score, reverse=True)
        top_results = results[:top_k]

        # 4. Cognitive Side-Effects
        if top_results:
            recalled_tags: Set[str] = set()
            for res in top_results:
                # Increment access count
                self.storage.record_access(res.memory.id, timestamp=now)
                # Check for systems consolidation candidate
                if res.memory.access_count >= 5:
                    self.consolidate_memory(res.memory)
                # Push into DLPFC working memory
                if auto_activate_working_memory:
                    self.working_memory.put(res.memory)
                recalled_tags.update(res.memory.tags)

            # Reinforce STDP co-activation
            if auto_reinforce_stdp and recalled_tags:
                all_active_tags = list(recalled_tags.union(query_tokens))
                self.record_coactivation(all_active_tags, timestamp=now)

        return top_results
