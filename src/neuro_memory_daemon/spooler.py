"""Autonomous live agent activity spooler for neuro-memory-daemon.

Monitors and auto-spools live agent events from:
1. Google Antigravity transcripts (~/.gemini/antigravity-cli/brain/*/transcript.jsonl)
2. Grok chat history sessions (~/.grok/sessions/*/*/chat_history.jsonl)
3. Zoth Civilization colony state & subconscious thoughts (~/NullAITech/zoth-civilization/data/)

Transforms live agent turns, tool executions, and autonomous thoughts into
synaptic engrams, triggers biological spreading activation, and broadcasts
action potentials to the 3D Cosmic Neural Nebula in real time.
Pure Python standard library implementation.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from neuro_memory_daemon import MemoryDaemon, get_default_daemon


class AgentSpooler:
    """Background daemon thread monitoring active agent files and feeding the neural substrate."""

    def __init__(
        self,
        daemon: Optional[MemoryDaemon] = None,
        poll_interval: float = 20.0,
        max_tail_bytes: int = 16384,
    ) -> None:
        self.daemon = daemon or get_default_daemon()
        self.poll_interval = poll_interval
        self.max_tail_bytes = max_tail_bytes

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_offsets: Dict[str, int] = {}
        self._seen_hashes: Set[str] = set()
        self._civ_last_mtime: float = 0.0

        # Base directories
        self.home = Path.home()
        self.antigravity_dir = self.home / ".gemini" / "antigravity-cli" / "brain"
        self.grok_dir = self.home / ".grok" / "sessions"
        self.civ_dir = self.home / "NullAITech" / "zoth-civilization" / "data"

    def start(self) -> None:
        """Start the background spooler thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._spool_loop, daemon=True, name="neuro-spooler")
        self._thread.start()

    def stop(self) -> None:
        """Stop the background spooler thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _spool_loop(self) -> None:
        """Continuous polling loop scanning active agent directories."""
        # Initial offset calibration to avoid flooding historic logs
        self._initialize_offsets()

        while self._running:
            try:
                self._poll_antigravity()
                self._poll_grok()
                self._poll_civilization()
            except Exception as e:
                # Suppress errors to ensure spooler resilience
                pass

            time.sleep(self.poll_interval)

    def _initialize_offsets(self) -> None:
        """Seek existing files to end so only new live activity triggers action potentials."""
        # 1. Antigravity transcripts
        if self.antigravity_dir.exists():
            pattern = str(self.antigravity_dir / "*" / "transcript.jsonl")
            for fpath in glob.glob(pattern):
                try:
                    self._file_offsets[fpath] = os.path.getsize(fpath)
                except OSError:
                    pass

        # 2. Grok sessions
        if self.grok_dir.exists():
            pattern = str(self.grok_dir / "*" / "*" / "chat_history.jsonl")
            for fpath in glob.glob(pattern):
                try:
                    self._file_offsets[fpath] = os.path.getsize(fpath)
                except OSError:
                    pass

        # 3. Civilization subconscious
        civ_subc = self.civ_dir / "agent_subconscious.json"
        if civ_subc.exists():
            try:
                self._civ_last_mtime = civ_subc.stat().st_mtime
            except OSError:
                pass

    def _poll_antigravity(self) -> None:
        """Scan active Antigravity session transcripts."""
        if not self.antigravity_dir.exists():
            return

        # Find transcripts modified in the last 15 minutes
        now = time.time()
        pattern = str(self.antigravity_dir / "*" / "transcript.jsonl")
        for fpath in glob.glob(pattern):
            try:
                stat = os.stat(fpath)
                if now - stat.st_mtime > 900:  # older than 15 mins
                    continue

                prev_offset = self._file_offsets.get(fpath, max(0, stat.st_size - 4096))
                if stat.st_size > prev_offset:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(prev_offset)
                        new_content = f.read()
                        self._file_offsets[fpath] = f.tell()

                    for line in new_content.splitlines():
                        line_str = line.strip()
                        if not line_str:
                            continue
                        self._process_antigravity_turn(line_str)
            except Exception:
                pass

    def _process_antigravity_turn(self, line: str) -> None:
        """Process a single transcript JSONL line from Antigravity."""
        try:
            item = json.loads(line)
        except Exception:
            return

        item_type = item.get("type", "")
        # Look for user inputs, planner responses, and tool calls
        if item_type not in ("USER_INPUT", "PLANNER_RESPONSE"):
            return

        content = str(item.get("content") or "")
        thinking = str(item.get("thinking") or "")
        tool_calls = item.get("tool_calls") or []

        text_to_ingest = ""
        tags = ["antigravity", "agent"]

        if item_type == "USER_INPUT" and content:
            text_to_ingest = f"User instruction to Antigravity: {content[:180]}"
            tags.extend(["user_prompt", "intent"])
        elif item_type == "PLANNER_RESPONSE":
            if tool_calls and isinstance(tool_calls, list):
                tools_used = [tc.get("name") or tc.get("tool_name", "") for tc in tool_calls if isinstance(tc, dict)]
                tools_used = [t for t in tools_used if t]
                if tools_used:
                    text_to_ingest = f"Antigravity executed tools: {', '.join(tools_used)}"
                    tags.extend(["tool_execution"] + tools_used[:3])
            elif thinking:
                text_to_ingest = f"Antigravity cognitive deliberation: {thinking[:180]}"
                tags.extend(["deliberation", "reasoning"])
            elif content:
                text_to_ingest = f"Antigravity response: {content[:180]}"
                tags.extend(["assistant_turn"])

        if not text_to_ingest:
            return

        h = hashlib.sha256(text_to_ingest.encode("utf-8")).hexdigest()
        if h in self._seen_hashes:
            return
        self._seen_hashes.add(h)

        # Ingest and fire spreading activation
        res = self.daemon.store(
            text=text_to_ingest,
            tags=tags,
            importance=0.85,
            category="architecture" if "tool" in tags else "episodic",
            perspective="agent",
            agent_id="antigravity",
            metadata={"source": "antigravity_transcript", "spooled_at": time.time()},
        )
        self.daemon.trigger(res["id"], decay=0.8, threshold=0.25, max_hops=1)

    def _poll_grok(self) -> None:
        """Scan active Grok chat history sessions."""
        if not self.grok_dir.exists():
            return

        now = time.time()
        pattern = str(self.grok_dir / "*" / "*" / "chat_history.jsonl")
        for fpath in glob.glob(pattern):
            try:
                stat = os.stat(fpath)
                if now - stat.st_mtime > 900:
                    continue

                prev_offset = self._file_offsets.get(fpath, max(0, stat.st_size - 4096))
                if stat.st_size > prev_offset:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(prev_offset)
                        new_content = f.read()
                        self._file_offsets[fpath] = f.tell()

                    for line in new_content.splitlines():
                        line_str = line.strip()
                        if not line_str:
                            continue
                        self._process_grok_turn(line_str)
            except Exception:
                pass

    def _process_grok_turn(self, line: str) -> None:
        """Process a single chat history JSONL line from Grok."""
        try:
            item = json.loads(line)
        except Exception:
            return

        role = item.get("role", "")
        content = str(item.get("content") or "")
        if not content:
            return

        h = hashlib.sha256((role + ":" + content[:100]).encode("utf-8")).hexdigest()
        if h in self._seen_hashes:
            return
        self._seen_hashes.add(h)

        clean_text = f"Grok {role}: {content[:180]}"
        tags = ["grok", "agent", role]
        res = self.daemon.store(
            text=clean_text,
            tags=tags,
            importance=0.8,
            category="episodic",
            perspective="agent",
            agent_id="grok",
            metadata={"source": "grok_session", "spooled_at": time.time()},
        )
        self.daemon.trigger(res["id"], decay=0.8, threshold=0.25, max_hops=1)

    def _poll_civilization(self) -> None:
        """Scan Zoth Civilization autonomous colony reflections."""
        civ_subc = self.civ_dir / "agent_subconscious.json"
        if not civ_subc.exists():
            return

        try:
            stat = civ_subc.stat()
            if stat.st_mtime <= self._civ_last_mtime:
                return
            self._civ_last_mtime = stat.st_mtime

            with open(civ_subc, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            if isinstance(data, dict):
                # Process latest subconscious thoughts of agents
                for agent_name, thought_data in list(data.items())[:5]:
                    thought_text = ""
                    if isinstance(thought_data, str):
                        thought_text = thought_data
                    elif isinstance(thought_data, dict):
                        thought_text = thought_data.get("thought") or thought_data.get("reflection") or ""

                    if thought_text:
                        h = hashlib.sha256(f"{agent_name}:{thought_text[:80]}".encode("utf-8")).hexdigest()
                        if h not in self._seen_hashes:
                            self._seen_hashes.add(h)
                            res = self.daemon.store(
                                text=f"Civilization Mind [{agent_name}]: {thought_text[:180]}",
                                tags=["civilization", "living_mind", agent_name.lower()],
                                importance=0.9,
                                category="insight",
                                perspective="agent",
                                agent_id=f"civ_{agent_name.lower()}",
                                metadata={"source": "civilization_subconscious"},
                            )
                            self.daemon.trigger(res["id"], decay=0.85, threshold=0.25, max_hops=1)
        except Exception:
            pass


_GLOBAL_SPOOLER: Optional[AgentSpooler] = None


def get_global_spooler(daemon: Optional[MemoryDaemon] = None) -> AgentSpooler:
    """Retrieve or create the singleton agent spooler instance."""
    global _GLOBAL_SPOOLER
    if _GLOBAL_SPOOLER is None:
        _GLOBAL_SPOOLER = AgentSpooler(daemon=daemon)
    return _GLOBAL_SPOOLER


def start_spooler(daemon: Optional[MemoryDaemon] = None) -> AgentSpooler:
    """Start the global agent spooler in a background thread."""
    spooler = get_global_spooler(daemon=daemon)
    spooler.start()
    return spooler
