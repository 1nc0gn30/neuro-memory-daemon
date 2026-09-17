"""Persistent storage engine for neuro-memory-daemon.

Provides a robust SQLite-backed storage engine with thread safety, WAL journaling,
in-memory fallback, transaction management, and full serialization support for
memory traces and synaptic connection topologies.
Zero external dependencies (pure Python standard library).
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
import time
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from neuro_memory_daemon.compat import (
    atomic_write,
    ensure_dir,
    normalize_path,
    safe_read_json,
    safe_write_json,
)

# Standard memory categories
VALID_CATEGORIES = {
    "debug",
    "security",
    "architecture",
    "general",
    "tool",
    "insight",
    "episodic",
    "semantic",
    "procedure",
}


def calculate_shannon_entropy(text: str) -> float:
    """Calculate normalized Shannon entropy score (0.0 to 1.0) for information density.

    Args:
        text: Input string to evaluate.

    Returns:
        Entropy score between 0.0 and 1.0 rounded to 4 decimal places.
    """
    if not text or not text.strip():
        return 0.0

    cleaned = text.strip()
    length = len(cleaned)
    if length <= 1:
        return 0.0

    counts = Counter(cleaned)
    entropy = -sum((count / length) * math.log2(count / length) for count in counts.values())

    # Theoretical maximum entropy for character set in the sample
    max_possible = math.log2(min(len(counts), 128)) if len(counts) > 1 else 1.0
    normalized = min(1.0, max(0.0, entropy / max(max_possible, 1.0)))
    return round(normalized, 4)


def normalize_tags(tags: Optional[Union[List[str], Set[str], str]]) -> List[str]:
    """Clean, lowercase, strip, and deduplicate tag lists."""
    if tags is None:
        return []
    if isinstance(tags, str):
        raw_items = [t.strip() for t in tags.replace(",", " ").split() if t.strip()]
    else:
        raw_items = [str(t).strip() for t in tags if str(t).strip()]

    seen: Set[str] = set()
    cleaned: List[str] = []
    for item in raw_items:
        normalized = item.lower().lstrip("#")
        if normalized and normalized not in seen:
            seen.add(normalized)
            cleaned.append(normalized)
    return cleaned


@dataclass
class MemoryRecord:
    """Cognitive memory trace record.

    Attributes:
        id: Unique identifier for the memory record.
        agent_id: Identifier of the agent originating or owning the memory.
        perspective: Perspective tag (e.g. 'user', 'assistant', 'agent', 'observation').
        text: Raw text content of the memory trace.
        tags: List of semantic/associative tags.
        category: Category classification ('debug', 'security', 'architecture', etc.).
        entropy_score: Information density score (Shannon entropy, 0.0 - 1.0).
        importance: Base importance weight (0.0 to 1.0+).
        access_count: Total retrieval and access count.
        last_accessed_at: Unix timestamp of the most recent access.
        created_at: Unix timestamp of memory creation.
        decay_factor: Multiplier for Ebbinghaus decay resistance (default: 1.0).
        immutable: If True, immune to pruning and passive decay eviction.
        metadata: Arbitrary key-value metadata dictionary.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = "default"
    perspective: str = "agent"
    text: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    entropy_score: float = 0.0
    importance: float = 1.0
    access_count: int = 0
    last_accessed_at: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    decay_factor: float = 1.0
    immutable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.tags = normalize_tags(self.tags)
        if self.category not in VALID_CATEGORIES and self.category.lower() in VALID_CATEGORIES:
            self.category = self.category.lower()
        if self.entropy_score == 0.0 and self.text:
            self.entropy_score = calculate_shannon_entropy(self.text)
        if self.last_accessed_at == 0.0:
            self.last_accessed_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "perspective": self.perspective,
            "text": self.text,
            "tags": list(self.tags),
            "category": self.category,
            "entropy_score": float(self.entropy_score),
            "importance": float(self.importance),
            "access_count": int(self.access_count),
            "last_accessed_at": float(self.last_accessed_at),
            "created_at": float(self.created_at),
            "decay_factor": float(self.decay_factor),
            "immutable": bool(self.immutable),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryRecord:
        """Construct MemoryRecord from a dictionary."""
        tags = data.get("tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = normalize_tags(tags)

        metadata = data.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = {}

        return cls(
            id=str(data.get("id", str(uuid.uuid4()))),
            agent_id=str(data.get("agent_id", "default")),
            perspective=str(data.get("perspective", "agent")),
            text=str(data.get("text", "")),
            tags=normalize_tags(tags),
            category=str(data.get("category", "general")),
            entropy_score=float(data.get("entropy_score", 0.0)),
            importance=float(data.get("importance", 1.0)),
            access_count=int(data.get("access_count", 0)),
            last_accessed_at=float(data.get("last_accessed_at", time.time())),
            created_at=float(data.get("created_at", time.time())),
            decay_factor=float(data.get("decay_factor", 1.0)),
            immutable=bool(data.get("immutable", False)),
            metadata=metadata if isinstance(metadata, dict) else {},
        )


@dataclass
class SynapseRecord:
    """Synaptic link representing plastic associative weight between entities.

    Attributes:
        source: Origin node identifier (tag or memory ID).
        target: Destination node identifier (tag or memory ID).
        weight: Synaptic strength weight (0.0 to 1.0+).
        co_occurrence_count: Cumulative co-activation frequency.
        last_stimulated_at: Timestamp of last spike/co-activation.
        synapse_type: Category of synapse ('tag_tag', 'memory_memory', 'memory_tag').
    """

    source: str
    target: str
    weight: float = 0.1
    co_occurrence_count: int = 1
    last_stimulated_at: float = field(default_factory=time.time)
    synapse_type: str = "tag_tag"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "target": self.target,
            "weight": round(float(self.weight), 4),
            "co_occurrence_count": int(self.co_occurrence_count),
            "last_stimulated_at": float(self.last_stimulated_at),
            "synapse_type": self.synapse_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SynapseRecord:
        """Create SynapseRecord from dictionary."""
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            weight=float(data.get("weight", 0.1)),
            co_occurrence_count=int(data.get("co_occurrence_count", 1)),
            last_stimulated_at=float(data.get("last_stimulated_at", time.time())),
            synapse_type=str(data.get("synapse_type", "tag_tag")),
        )


class StorageEngine:
    """Thread-safe persistent SQLite storage engine with in-memory fallback.

    Handles high-performance atomic storage for cognitive memory traces,
    synaptic association links, and relational tag indexing.
    """

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        in_memory: bool = False,
    ) -> None:
        """Initialize StorageEngine.

        Args:
            db_path: Path to the SQLite database file. If None or in_memory is True,
                     an in-memory database (:memory:) is created.
            in_memory: If True, explicitly forces an in-memory SQLite database.
        """
        self._lock = threading.RLock()
        self.is_in_memory = in_memory or db_path is None or str(db_path) == ":memory:"

        if self.is_in_memory:
            self.db_path: Optional[Path] = None
            self._conn_str = ":memory:"
        else:
            try:
                self.db_path = normalize_path(db_path)
                ensure_dir(self.db_path.parent)
                self._conn_str = str(self.db_path)
            except Exception:
                # Fallback to in-memory on filesystem failure
                self.db_path = None
                self._conn_str = ":memory:"
                self.is_in_memory = True

        self._conn = sqlite3.connect(
            self._conn_str,
            check_same_thread=False,
            timeout=30.0,
        )
        self._conn.row_factory = sqlite3.Row

        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables, pragmas, and indexes."""
        with self._lock, self._conn:
            cursor = self._conn.cursor()
            if not self.is_in_memory:
                try:
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")
                except sqlite3.OperationalError:
                    pass

            cursor.execute("PRAGMA foreign_keys=ON;")

            # 1. Memories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    perspective TEXT NOT NULL,
                    text TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    category TEXT NOT NULL,
                    entropy_score REAL NOT NULL DEFAULT 0.0,
                    importance REAL NOT NULL DEFAULT 1.0,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed_at REAL NOT NULL,
                    created_at REAL NOT NULL,
                    decay_factor REAL NOT NULL DEFAULT 1.0,
                    immutable INTEGER NOT NULL DEFAULT 0,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );
                """
            )

            # 2. Synapses table (directional weighted links)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS synapses (
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 0.1,
                    co_occurrence_count INTEGER NOT NULL DEFAULT 1,
                    last_stimulated_at REAL NOT NULL,
                    synapse_type TEXT NOT NULL DEFAULT 'tag_tag',
                    PRIMARY KEY (source, target, synapse_type)
                );
                """
            )

            # 3. Memory-Tag junction table for fast relational index
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_tags (
                    memory_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (memory_id, tag),
                    FOREIGN KEY (memory_id) REFERENCES memories (id) ON DELETE CASCADE
                );
                """
            )

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_cat ON memories(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_accessed ON memories(last_accessed_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_synapses_src ON synapses(source);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_synapses_tgt ON synapses(target);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_synapses_weight ON synapses(weight);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memtags_tag ON memory_tags(tag);")

    def save_memory(self, record: MemoryRecord) -> str:
        """Insert or replace a memory trace in persistent storage.

        Args:
            record: MemoryRecord instance to persist.

        Returns:
            Memory ID string.
        """
        with self._lock, self._conn:
            cursor = self._conn.cursor()
            tags_json = json.dumps(record.tags)
            meta_json = json.dumps(record.metadata, default=str)

            cursor.execute(
                """
                INSERT INTO memories (
                    id, agent_id, perspective, text, tags, category,
                    entropy_score, importance, access_count, last_accessed_at,
                    created_at, decay_factor, immutable, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    agent_id=excluded.agent_id,
                    perspective=excluded.perspective,
                    text=excluded.text,
                    tags=excluded.tags,
                    category=excluded.category,
                    entropy_score=excluded.entropy_score,
                    importance=excluded.importance,
                    access_count=excluded.access_count,
                    last_accessed_at=excluded.last_accessed_at,
                    created_at=excluded.created_at,
                    decay_factor=excluded.decay_factor,
                    immutable=excluded.immutable,
                    metadata=excluded.metadata;
                """,
                (
                    record.id,
                    record.agent_id,
                    record.perspective,
                    record.text,
                    tags_json,
                    record.category,
                    record.entropy_score,
                    record.importance,
                    record.access_count,
                    record.last_accessed_at,
                    record.created_at,
                    record.decay_factor,
                    1 if record.immutable else 0,
                    meta_json,
                ),
            )

            # Update memory_tags junction table
            cursor.execute("DELETE FROM memory_tags WHERE memory_id = ?;", (record.id,))
            for tag in record.tags:
                cursor.execute(
                    "INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?, ?);",
                    (record.id, tag),
                )

        return record.id

    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        """Retrieve a memory trace by its unique ID.

        Args:
            memory_id: Target memory identifier.

        Returns:
            MemoryRecord or None if not found.
        """
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?;", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_memory(row)

    def update_memory(self, memory_id: str, **kwargs: Any) -> Optional[MemoryRecord]:
        """Update specific fields of an existing memory trace.

        Args:
            memory_id: Target memory identifier.
            **kwargs: Attributes to update (e.g. text, tags, importance, access_count).

        Returns:
            Updated MemoryRecord or None if memory not found.
        """
        existing = self.get_memory(memory_id)
        if not existing:
            return None

        for k, v in kwargs.items():
            if hasattr(existing, k):
                setattr(existing, k, v)

        existing.__post_init__()
        self.save_memory(existing)
        return existing

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory trace and associated tags by ID.

        Args:
            memory_id: Target memory identifier.

        Returns:
            True if a record was deleted, False otherwise.
        """
        with self._lock, self._conn:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM memory_tags WHERE memory_id = ?;", (memory_id,))
            cursor.execute("DELETE FROM memories WHERE id = ?;", (memory_id,))
            return cursor.rowcount > 0

    def record_access(self, memory_id: str, timestamp: Optional[float] = None) -> Optional[MemoryRecord]:
        """Increment access count and refresh last_accessed_at timestamp.

        Args:
            memory_id: Target memory identifier.
            timestamp: Optional timestamp (defaults to current time).

        Returns:
            Updated MemoryRecord or None if not found.
        """
        ts = timestamp if timestamp is not None else time.time()
        with self._lock, self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                UPDATE memories
                SET access_count = access_count + 1, last_accessed_at = ?
                WHERE id = ?;
                """,
                (ts, memory_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_memory(memory_id)

    def list_memories(
        self,
        agent_id: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        ascending: bool = False,
    ) -> List[MemoryRecord]:
        """List and filter memory records with pagination.

        Args:
            agent_id: Optional agent ID filter.
            category: Optional category filter.
            tag: Optional tag filter.
            limit: Maximum items to return.
            offset: Offset for pagination.
            sort_by: Column to sort by ('created_at', 'last_accessed_at', 'importance', 'access_count').
            ascending: Sort direction (True for ASC, False for DESC).

        Returns:
            List of matching MemoryRecord objects.
        """
        allowed_sorts = {"created_at", "last_accessed_at", "importance", "access_count", "entropy_score"}
        col = sort_by if sort_by in allowed_sorts else "created_at"
        order = "ASC" if ascending else "DESC"

        query = ["SELECT m.* FROM memories m"]
        params: List[Any] = []
        where_clauses: List[str] = []

        if tag:
            query.append("JOIN memory_tags mt ON m.id = mt.memory_id")
            where_clauses.append("mt.tag = ?")
            params.append(tag.lower().strip().lstrip("#"))

        if agent_id:
            where_clauses.append("m.agent_id = ?")
            params.append(agent_id)

        if category:
            where_clauses.append("m.category = ?")
            params.append(category.lower().strip())

        if where_clauses:
            query.append("WHERE " + " AND ".join(where_clauses))

        query.append(f"ORDER BY m.{col} {order} LIMIT ? OFFSET ?;")
        params.extend([max(1, limit), max(0, offset)])

        sql = " ".join(query)
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_memory(r) for r in rows]

    def get_all_memories(self, agent_id: Optional[str] = None) -> List[MemoryRecord]:
        """Retrieve all memories in storage, optionally filtered by agent_id."""
        return self.list_memories(agent_id=agent_id, limit=1000000)

    def count_memories(
        self,
        agent_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """Count total memories matching criteria."""
        query = ["SELECT COUNT(*) FROM memories"]
        params: List[Any] = []
        where: List[str] = []

        if agent_id:
            where.append("agent_id = ?")
            params.append(agent_id)
        if category:
            where.append("category = ?")
            params.append(category.lower().strip())

        if where:
            query.append("WHERE " + " AND ".join(where))

        sql = " ".join(query)
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def search_text(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[MemoryRecord]:
        """Search memories containing text keywords using SQL LIKE."""
        if not query or not query.strip():
            return []

        pattern = f"%{query.strip()}%"
        sql = "SELECT * FROM memories WHERE text LIKE ?"
        params: List[Any] = [pattern]

        if agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)

        sql += " ORDER BY last_accessed_at DESC LIMIT ?;"
        params.append(max(1, limit))

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_memory(r) for r in rows]

    def prune_memories(self, memory_ids: List[str]) -> int:
        """Delete memories by ID list, skipping immutable memories.

        Args:
            memory_ids: List of candidate memory IDs to prune.

        Returns:
            Number of memories deleted.
        """
        if not memory_ids:
            return 0

        placeholders = ",".join("?" for _ in memory_ids)
        with self._lock, self._conn:
            cursor = self._conn.cursor()
            # Delete only non-immutable
            cursor.execute(
                f"""
                DELETE FROM memories
                WHERE id IN ({placeholders}) AND immutable = 0;
                """,
                memory_ids,
            )
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                # Cleanup orphaned memory_tags
                cursor.execute(
                    "DELETE FROM memory_tags WHERE memory_id NOT IN (SELECT id FROM memories);"
                )
            return deleted_count

    # -------------------------------------------------------------------------
    # Synapse Storage Management
    # -------------------------------------------------------------------------

    def save_synapse(
        self,
        source: str,
        target: str,
        weight: float,
        synapse_type: str = "tag_tag",
        timestamp: Optional[float] = None,
        co_occur_delta: int = 1,
    ) -> SynapseRecord:
        """Save or reinforce a synaptic link between two nodes.

        Args:
            source: Source node identifier.
            target: Target node identifier.
            weight: Synaptic connection weight (0.0 to 1.0+).
            synapse_type: Type of connection.
            timestamp: Last stimulated timestamp.
            co_occur_delta: Increment to co_occurrence_count.

        Returns:
            Saved SynapseRecord.
        """
        ts = timestamp if timestamp is not None else time.time()
        src = source.strip().lower()
        tgt = target.strip().lower()
        clamped_weight = max(0.0, float(weight))

        with self._lock, self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO synapses (
                    source, target, weight, co_occurrence_count,
                    last_stimulated_at, synapse_type
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, target, synapse_type) DO UPDATE SET
                    weight = excluded.weight,
                    co_occurrence_count = synapses.co_occurrence_count + excluded.co_occurrence_count,
                    last_stimulated_at = excluded.last_stimulated_at;
                """,
                (src, tgt, clamped_weight, max(1, co_occur_delta), ts, synapse_type),
            )

        return SynapseRecord(
            source=src,
            target=tgt,
            weight=clamped_weight,
            co_occurrence_count=co_occur_delta,
            last_stimulated_at=ts,
            synapse_type=synapse_type,
        )

    def get_synapse(
        self,
        source: str,
        target: str,
        synapse_type: str = "tag_tag",
    ) -> Optional[SynapseRecord]:
        """Retrieve a specific synaptic connection."""
        src = source.strip().lower()
        tgt = target.strip().lower()
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT * FROM synapses
                WHERE source = ? AND target = ? AND synapse_type = ?;
                """,
                (src, tgt, synapse_type),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return SynapseRecord(
                source=row["source"],
                target=row["target"],
                weight=float(row["weight"]),
                co_occurrence_count=int(row["co_occurrence_count"]),
                last_stimulated_at=float(row["last_stimulated_at"]),
                synapse_type=row["synapse_type"],
            )

    def get_synapses_for_node(
        self,
        node: str,
        min_weight: float = 0.0,
        limit: int = 100,
    ) -> List[SynapseRecord]:
        """Get all synapses connected to or from a node above min_weight."""
        n = node.strip().lower()
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT * FROM synapses
                WHERE (source = ? OR target = ?) AND weight >= ?
                ORDER BY weight DESC LIMIT ?;
                """,
                (n, n, float(min_weight), max(1, limit)),
            )
            rows = cursor.fetchall()
            return [
                SynapseRecord(
                    source=r["source"],
                    target=r["target"],
                    weight=float(r["weight"]),
                    co_occurrence_count=int(r["co_occurrence_count"]),
                    last_stimulated_at=float(r["last_stimulated_at"]),
                    synapse_type=r["synapse_type"],
                )
                for r in rows
            ]

    def get_all_synapses(self, min_weight: float = 0.0) -> List[SynapseRecord]:
        """Retrieve all active synapses above a minimum weight."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT * FROM synapses
                WHERE weight >= ?
                ORDER BY weight DESC;
                """,
                (float(min_weight),),
            )
            rows = cursor.fetchall()
            return [
                SynapseRecord(
                    source=r["source"],
                    target=r["target"],
                    weight=float(r["weight"]),
                    co_occurrence_count=int(r["co_occurrence_count"]),
                    last_stimulated_at=float(r["last_stimulated_at"]),
                    synapse_type=r["synapse_type"],
                )
                for r in rows
            ]

    def prune_synapses(self, min_weight: float = 0.01) -> int:
        """Prune degraded synapses falling below min_weight threshold."""
        with self._lock, self._conn:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM synapses WHERE weight < ?;", (float(min_weight),))
            return cursor.rowcount

    def decay_all_synapses(self, decay_rate: float, elapsed_seconds: float) -> int:
        """Apply passive exponential decay to all synapses.

        w_new = w * exp(-decay_rate * elapsed_seconds)
        """
        if elapsed_seconds <= 0 or decay_rate <= 0:
            return 0

        factor = math.exp(-decay_rate * elapsed_seconds)
        with self._lock, self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                "UPDATE synapses SET weight = weight * ?;",
                (factor,),
            )
            return cursor.rowcount

    def delete_synapses_for_node(self, node: str) -> int:
        """Delete all synaptic connections associated with a node."""
        n = node.strip().lower()
        with self._lock, self._conn:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM synapses WHERE source = ? OR target = ?;", (n, n))
            return cursor.rowcount

    # -------------------------------------------------------------------------
    # Journal & Import / Export
    # -------------------------------------------------------------------------

    def export_journal(self) -> Dict[str, Any]:
        """Export all memories and synapses as a structured serializable dictionary."""
        memories = [m.to_dict() for m in self.get_all_memories()]
        synapses = [s.to_dict() for s in self.get_all_synapses()]
        return {
            "version": "1.0.0",
            "exported_at": time.time(),
            "memories_count": len(memories),
            "synapses_count": len(synapses),
            "memories": memories,
            "synapses": synapses,
        }

    def import_journal(self, data: Dict[str, Any], overwrite: bool = False) -> int:
        """Import memories and synapses from a journal dictionary.

        Args:
            data: Journal dictionary containing 'memories' and optional 'synapses'.
            overwrite: If True, clears existing tables before importing.

        Returns:
            Count of memories successfully imported.
        """
        with self._lock, self._conn:
            if overwrite:
                cursor = self._conn.cursor()
                cursor.execute("DELETE FROM memory_tags;")
                cursor.execute("DELETE FROM memories;")
                cursor.execute("DELETE FROM synapses;")

            imported_count = 0
            for item in data.get("memories", []):
                try:
                    record = MemoryRecord.from_dict(item)
                    self.save_memory(record)
                    imported_count += 1
                except Exception:
                    continue

            for syn in data.get("synapses", []):
                try:
                    self.save_synapse(
                        source=syn["source"],
                        target=syn["target"],
                        weight=float(syn.get("weight", 0.1)),
                        synapse_type=syn.get("synapse_type", "tag_tag"),
                        timestamp=float(syn.get("last_stimulated_at", time.time())),
                        co_occur_delta=int(syn.get("co_occurrence_count", 1)),
                    )
                except Exception:
                    continue

            return imported_count

    def export_json_file(self, file_path: Union[str, Path]) -> Path:
        """Export storage content to an atomic JSON file."""
        data = self.export_journal()
        return safe_write_json(file_path, data, indent=2, atomic=True)

    def import_json_file(self, file_path: Union[str, Path], overwrite: bool = False) -> int:
        """Import storage content from a JSON file."""
        data = safe_read_json(file_path, default=None)
        if not data or not isinstance(data, dict):
            return 0
        return self.import_journal(data, overwrite=overwrite)

    def vacuum(self) -> None:
        """Optimize and vacuum SQLite database."""
        with self._lock:
            try:
                self._conn.execute("VACUUM;")
            except Exception:
                pass

    def close(self) -> None:
        """Close SQLite database connection cleanly."""
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                pass

    def __enter__(self) -> StorageEngine:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _row_to_memory(self, row: sqlite3.Row) -> MemoryRecord:
        """Helper to convert sqlite3.Row to MemoryRecord."""
        tags_raw = row["tags"]
        try:
            tags = json.loads(tags_raw) if tags_raw else []
        except Exception:
            tags = []

        meta_raw = row["metadata"]
        try:
            metadata = json.loads(meta_raw) if meta_raw else {}
        except Exception:
            metadata = {}

        return MemoryRecord(
            id=row["id"],
            agent_id=row["agent_id"],
            perspective=row["perspective"],
            text=row["text"],
            tags=tags,
            category=row["category"],
            entropy_score=float(row["entropy_score"]),
            importance=float(row["importance"]),
            access_count=int(row["access_count"]),
            last_accessed_at=float(row["last_accessed_at"]),
            created_at=float(row["created_at"]),
            decay_factor=float(row["decay_factor"]),
            immutable=bool(row["immutable"]),
            metadata=metadata,
        )
