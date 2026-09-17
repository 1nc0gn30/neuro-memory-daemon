"""Sleep-Replay Consolidation and Hippocampal-to-Neocortical Transfer Engine.

Simulates biological sleep stages (Slow-Wave Sleep / SWR Sharp-Wave Ripples)
to perform systems memory consolidation:
1. Replays high-valence episodic memories in compressed chronological bursts.
2. Identifies semantic concept cliques and establishes dense cross-synaptic links.
3. Automatically promotes durable episodic knowledge to neocortical semantic tier.
4. Safely prunes decayed sub-threshold memories whose retention dropped below critical levels.

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from neuro_memory_daemon.storage import MemoryRecord, StorageEngine, SynapseRecord
from neuro_memory_daemon.synapse_engine import SynapseEngine, compute_sparse_cosine_similarity


@dataclass
class SemanticSchemaCluster:
    """Consolidated conceptual schema cluster synthesized from episodic traces."""

    name: str
    tags: List[str]
    member_memory_ids: List[str]
    cohesion_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SleepReplayReport:
    """Telemetry report of a sleep consolidation and replay cycle."""

    replayed_memories_count: int
    consolidated_count: int
    pruned_decayed_count: int
    new_synapses_forged: int
    schemata_synthesized: List[Dict[str, Any]] = field(default_factory=list)
    average_retention_before: float = 0.0
    average_retention_after: float = 0.0
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_sleep_replay_consolidation(
    synapse_engine: SynapseEngine,
    agent_id: Optional[str] = None,
    min_retention_threshold: float = 0.15,
    replay_passes: int = 2,
    now: Optional[float] = None,
) -> SleepReplayReport:
    """Execute sleep consolidation pass across stored memory records.

    Args:
        synapse_engine: Active SynapseEngine instance.
        agent_id: Optional filter for a specific agent's memory domain.
        min_retention_threshold: Memory retention below which non-immutable records are pruned.
        replay_passes: Number of Sharp-Wave Ripple simulation iterations.
        now: Optional current timestamp override for deterministic testing.

    Returns:
        SleepReplayReport detailing consolidation and pruning metrics.
    """
    start_time = time.time()
    current_time = now if now is not None else start_time

    memories = synapse_engine.storage.list_memories(agent_id=agent_id, limit=1000)
    if not memories:
        return SleepReplayReport(
            replayed_memories_count=0,
            consolidated_count=0,
            pruned_decayed_count=0,
            new_synapses_forged=0,
            schemata_synthesized=[],
            average_retention_before=0.0,
            average_retention_after=0.0,
            duration_seconds=round(time.time() - start_time, 4),
        )

    # Initial retention statistics
    retentions_initial = [synapse_engine.calculate_retention(m, current_time=current_time) for m in memories]
    avg_retention_before = round(sum(retentions_initial) / len(retentions_initial), 3) if retentions_initial else 0.0

    replayed_count = 0
    consolidated_count = 0
    synapses_forged = 0
    schemata: List[SemanticSchemaCluster] = []

    # 1. Multi-pass Sharp Wave-Ripple Replay
    for _ in range(replay_passes):
        # Sort by importance and emotional valence
        replay_queue = sorted(memories, key=lambda m: (m.importance, m.access_count), reverse=True)
        for i in range(len(replay_queue)):
            mem_a = replay_queue[i]
            replayed_count += 1

            # Reinforce associations with proximate or overlapping memories
            for j in range(i + 1, min(i + 5, len(replay_queue))):
                mem_b = replay_queue[j]
                shared_tags = set(mem_a.tags).intersection(set(mem_b.tags))
                if shared_tags:
                    # Apply Hebbian STDP reinforcement between memory nodes
                    delta_t = abs(mem_a.last_accessed_at - mem_b.last_accessed_at)
                    synapse_engine.reinforce_synapse(
                        node_a=mem_a.id,
                        node_b=mem_b.id,
                        delta_t=delta_t,
                        synapse_type="memory_memory",
                        timestamp=current_time,
                    )
                    synapses_forged += 1

    # 2. Systems Consolidation (Episodic -> Semantic promotion)
    for mem in memories:
        if mem.access_count >= 3 or mem.importance >= 1.2:
            synapse_engine.consolidate_memory(mem)
            consolidated_count += 1

    # 3. Detect and Cluster Semantic Schemata based on Tag Cliques
    tag_to_memories: Dict[str, List[MemoryRecord]] = {}
    for mem in memories:
        for tag in mem.tags:
            tag_to_memories.setdefault(tag, []).append(mem)

    for tag, cluster in tag_to_memories.items():
        if len(cluster) >= 3:
            schemata.append(
                SemanticSchemaCluster(
                    name=f"Schema::{tag.capitalize()}",
                    tags=[tag],
                    member_memory_ids=[m.id for m in cluster],
                    cohesion_score=round(min(1.0, 0.5 + (len(cluster) * 0.1)), 2),
                )
            )

    # 4. Prune decayed sub-threshold traces
    pruned_count = 0
    for mem in memories:
        retention = synapse_engine.calculate_retention(mem, current_time=current_time)
        if retention < min_retention_threshold and not mem.immutable and mem.importance < 0.8:
            synapse_engine.storage.delete_memory(mem.id)
            pruned_count += 1

    # Remaining memories retention
    remaining_memories = synapse_engine.storage.list_memories(agent_id=agent_id, limit=1000)
    retentions_final = [synapse_engine.calculate_retention(m, current_time=current_time) for m in remaining_memories]
    avg_retention_after = round(sum(retentions_final) / len(retentions_final), 3) if retentions_final else 0.0

    return SleepReplayReport(
        replayed_memories_count=replayed_count,
        consolidated_count=consolidated_count,
        pruned_decayed_count=pruned_count,
        new_synapses_forged=synapses_forged,
        schemata_synthesized=[s.to_dict() for s in schemata[:5]],
        average_retention_before=avg_retention_before,
        average_retention_after=avg_retention_after,
        duration_seconds=round(time.time() - start_time, 4),
    )
