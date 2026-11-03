"""Read-only federation of local memory stores on this machine.

Surfaces Grok topics, Hermes MEMORY/SOUL, Zoth Bot per-bot notes, and AGY
soul files alongside a bounded slice of the Neuro substrate. Never writes.
Skips archives, binaries, locks, and filenames that look like secrets.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from neuro_memory_daemon.compat import normalize_path, safe_read_text

MAX_TEXT = 4000
MAX_PER_SOURCE = 200
DEFAULT_LIMIT = 80
NEURO_MIX_CAP = 8

SKIP_NAME_PARTS = (
    "secret",
    "token",
    "auth",
    "password",
    "credential",
    "cosign",
    ".lock",
)

SKIP_SUFFIXES = {
    ".sqlite",
    ".sqlite-wal",
    ".sqlite-shm",
    ".db",
    ".db-wal",
    ".db-shm",
    ".pyc",
    ".pyo",
    ".so",
    ".bin",
    ".key",
    ".pem",
    ".p12",
}

SOURCE_META = (
    ("neuro", "Neuro Substrate", "Synaptic engrams already in this daemon"),
    ("grok", "Grok", "Grok Build topics, indexes, and inbox observations"),
    ("hermes", "Hermes", "Hermes MEMORY.md and SOUL.md"),
    ("zoth-bot", "Zoth Bot", "Per-bot memory.md notes"),
    ("agy", "AGY", "Gemini/Antigravity soul notes"),
)


def _home(home: Optional[os.PathLike[str] | str] = None) -> Path:
    if home is not None:
        return normalize_path(home)
    override = os.environ.get("NEURO_EVERYWHERE_HOME", "").strip()
    if override:
        return normalize_path(override)
    return Path.home()


def _is_skipped(path: Path) -> bool:
    name = path.name.lower()
    if any(part in name for part in SKIP_NAME_PARTS):
        return True
    suffix = path.suffix.lower()
    if suffix in SKIP_SUFFIXES:
        return True
    # compound sqlite suffixes: file.sqlite-wal
    lowered = name
    if any(lowered.endswith(sfx) for sfx in SKIP_SUFFIXES):
        return True
    return False


def _display_path(path: Path, home: Path) -> str:
    try:
        rel = path.resolve().relative_to(home.resolve())
        return str(Path("~") / rel)
    except (ValueError, OSError):
        return str(path)


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        return text
    body = rest[end + 4 :]
    return body.lstrip("\n")


def _title_from_text(text: str, fallback: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("# "):
            return s[2:].strip()[:120]
        if s.startswith(">") or s.startswith("---") or s.startswith("schema_version"):
            continue
        if s.startswith("- **") and s.endswith("**"):
            return s.strip("- *")[:120]
        return s[:120]
    return fallback


def _mtime(path: Path) -> float:
    try:
        return float(path.stat().st_mtime)
    except OSError:
        return 0.0


def _item(
    *,
    source: str,
    path: Path,
    home: Path,
    text: str,
    tags: Sequence[str],
    scope: str = "",
    title: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cleaned = _strip_frontmatter(text or "")
    preview = cleaned[:MAX_TEXT]
    stem = path.stem if path.suffix else path.name
    resolved_title = title or _title_from_text(cleaned, stem.replace("-", " ").replace("_", " "))
    payload: Dict[str, Any] = {
        "id": f"{source}:{scope}:{path.name}" if scope else f"{source}:{path.name}",
        "source": source,
        "title": resolved_title,
        "text": preview,
        "truncated": len(cleaned) > MAX_TEXT,
        "path": _display_path(path, home),
        "mtime": _mtime(path),
        "tags": list(tags),
        "scope": scope,
        "bytes": len(cleaned.encode("utf-8")),
    }
    if extra:
        payload.update(extra)
    return payload


def _read_md(path: Path) -> str:
    if _is_skipped(path) or not path.is_file():
        return ""
    try:
        return safe_read_text(path)
    except (OSError, UnicodeError, ValueError):
        return ""


def _iter_md(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return
    try:
        for path in sorted(root.iterdir()):
            if path.is_file() and path.suffix.lower() == ".md" and not _is_skipped(path):
                yield path
    except OSError:
        return


def collect_grok(home: Path, include_archive: bool = False) -> List[Dict[str, Any]]:
    root = home / ".grok" / "memory-v2"
    items: List[Dict[str, Any]] = []
    if not root.is_dir():
        return items

    scopes: List[Tuple[str, Path]] = []
    global_dir = root / "global"
    if global_dir.is_dir():
        scopes.append(("global", global_dir))
    workspaces = root / "workspaces"
    if workspaces.is_dir():
        try:
            for ws in sorted(workspaces.iterdir()):
                if ws.is_dir():
                    scopes.append((ws.name, ws))
        except OSError:
            pass

    for scope, base in scopes:
        index = base / "MEMORY.md"
        if index.is_file() and not _is_skipped(index):
            text = _read_md(index)
            if text.strip():
                items.append(
                    _item(
                        source="grok",
                        path=index,
                        home=home,
                        text=text,
                        tags=["index"],
                        scope=scope,
                        title=f"Grok index · {scope}",
                    )
                )
        for topic in _iter_md(base / "topics"):
            text = _read_md(topic)
            if not text.strip():
                continue
            items.append(
                _item(
                    source="grok",
                    path=topic,
                    home=home,
                    text=text,
                    tags=["topic"],
                    scope=scope,
                )
            )
        for obs in _iter_md(base / "observations" / "_inbox"):
            text = _read_md(obs)
            if not text.strip():
                continue
            items.append(
                _item(
                    source="grok",
                    path=obs,
                    home=home,
                    text=text,
                    tags=["observation", "inbox"],
                    scope=scope,
                )
            )
        if include_archive:
            archive = base / "archive"
            if archive.is_dir():
                try:
                    for path in archive.rglob("*.md"):
                        if not path.is_file() or _is_skipped(path):
                            continue
                        text = _read_md(path)
                        if not text.strip():
                            continue
                        items.append(
                            _item(
                                source="grok",
                                path=path,
                                home=home,
                                text=text,
                                tags=["archive"],
                                scope=scope,
                            )
                        )
                        if len(items) >= MAX_PER_SOURCE:
                            break
                except OSError:
                    pass
        if len(items) >= MAX_PER_SOURCE:
            break
    return items[:MAX_PER_SOURCE]


def collect_hermes(home: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    memories = home / ".hermes" / "memories" / "MEMORY.md"
    if memories.is_file() and not _is_skipped(memories):
        text = _read_md(memories)
        if text.strip():
            items.append(
                _item(
                    source="hermes",
                    path=memories,
                    home=home,
                    text=text,
                    tags=["memory"],
                    title="Hermes MEMORY",
                )
            )
    soul = home / ".hermes" / "SOUL.md"
    if soul.is_file() and not _is_skipped(soul):
        text = _read_md(soul)
        if text.strip():
            items.append(
                _item(
                    source="hermes",
                    path=soul,
                    home=home,
                    text=text,
                    tags=["soul"],
                    title="Hermes SOUL",
                )
            )
    return items


def collect_zoth_bot(home: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    bots = home / ".config" / "zothos" / "zoth-bot" / "bots"
    if not bots.is_dir():
        return items
    try:
        bot_dirs = sorted(p for p in bots.iterdir() if p.is_dir())
    except OSError:
        return items
    for bot_dir in bot_dirs:
        mem = bot_dir / "memory.md"
        if not mem.is_file() or _is_skipped(mem):
            continue
        text = _read_md(mem)
        if not text.strip():
            continue
        items.append(
            _item(
                source="zoth-bot",
                path=mem,
                home=home,
                text=text,
                tags=["bot", bot_dir.name],
                scope=bot_dir.name,
                title=f"Zoth Bot · {bot_dir.name}",
            )
        )
        if len(items) >= MAX_PER_SOURCE:
            break
    return items


def collect_agy(home: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    candidates = [
        (home / ".gemini" / "config" / "GEMINI.md", ["soul"], "AGY GEMINI.md"),
        (home / ".gemini" / "GEMINI.md", ["soul"], "AGY GEMINI.md"),
        (home / ".gemini" / "antigravity-cli" / "memory.json", ["graph"], "AGY knowledge graph"),
        (home / ".mcp" / "memory.json", ["graph"], "MCP knowledge graph"),
    ]
    for path, tags, title in candidates:
        if not path.is_file() or _is_skipped(path):
            continue
        text = _read_md(path) if path.suffix.lower() == ".md" else ""
        if path.suffix.lower() == ".json":
            try:
                text = safe_read_text(path)
            except (OSError, UnicodeError, ValueError):
                text = ""
        if not text.strip():
            continue
        items.append(
            _item(
                source="agy",
                path=path,
                home=home,
                text=text,
                tags=tags,
                title=title,
            )
        )
    return items


def _neuro_from_daemon(daemon: Any, query: str, limit: int) -> List[Dict[str, Any]]:
    if daemon is None:
        return []
    records: List[Dict[str, Any]] = []
    try:
        if query:
            raw = daemon.search(query=query, limit=limit) or []
        else:
            nodes = list(getattr(daemon, "nodes", {}).values())
            nodes.sort(key=lambda n: getattr(n, "created_at", 0), reverse=True)
            raw = [n.to_dict() if hasattr(n, "to_dict") else n for n in nodes[:limit]]
    except Exception:
        return []
    for rec in raw[:limit]:
        if not isinstance(rec, dict):
            continue
        text = str(rec.get("text") or rec.get("human_digest") or "")
        mem_id = str(rec.get("id") or "")
        records.append(
            {
                "id": f"neuro:{mem_id}",
                "source": "neuro",
                "title": (text.splitlines()[0] if text else mem_id)[:120],
                "text": text[:MAX_TEXT],
                "truncated": len(text) > MAX_TEXT,
                "path": "neuro-substrate",
                "mtime": float(rec.get("updated_at") or rec.get("created_at") or 0),
                "tags": list(rec.get("tags") or []),
                "scope": str(rec.get("agent_id") or rec.get("category") or ""),
                "bytes": len(text.encode("utf-8")),
                "category": rec.get("category"),
                "agent_id": rec.get("agent_id"),
                "neuro_id": mem_id,
            }
        )
    return records


def _neuro_count(daemon: Any) -> int:
    if daemon is None:
        return 0
    try:
        nodes = getattr(daemon, "nodes", None)
        if nodes is not None:
            return len(nodes)
        stats = daemon.get_stats()
        return int(stats.get("total_memories") or 0)
    except Exception:
        return 0


def _matches_query(item: Dict[str, Any], query: str) -> bool:
    if not query:
        return True
    q = query.lower()
    hay = " ".join(
        [
            str(item.get("title") or ""),
            str(item.get("text") or ""),
            str(item.get("path") or ""),
            str(item.get("scope") or ""),
            " ".join(item.get("tags") or []),
        ]
    ).lower()
    return q in hay


def collect(
    *,
    home: Optional[os.PathLike[str] | str] = None,
    daemon: Any = None,
    source: str = "",
    query: str = "",
    limit: int = DEFAULT_LIMIT,
    include_archive: bool = False,
) -> Dict[str, Any]:
    """Return source summaries plus a bounded item list.

    `source` is one of neuro|grok|hermes|zoth-bot|agy or empty for all.
    """
    root = _home(home)
    wanted = (source or "").strip().lower()
    q = (query or "").strip()
    try:
        cap = max(1, min(int(limit), MAX_PER_SOURCE))
    except (TypeError, ValueError):
        cap = DEFAULT_LIMIT

    grok_items = collect_grok(root, include_archive=include_archive)
    hermes_items = collect_hermes(root)
    bot_items = collect_zoth_bot(root)
    agy_items = collect_agy(root)

    file_by_source = {
        "grok": grok_items,
        "hermes": hermes_items,
        "zoth-bot": bot_items,
        "agy": agy_items,
    }

    neuro_limit = cap if wanted in ("", "neuro") else 0
    if wanted == "":
        neuro_limit = min(NEURO_MIX_CAP, cap)
    neuro_items = _neuro_from_daemon(daemon, q if wanted == "neuro" else "", neuro_limit) if neuro_limit else []
    if wanted == "neuro" and q:
        # already filtered by daemon.search
        pass
    elif q and neuro_items:
        neuro_items = [it for it in neuro_items if _matches_query(it, q)]

    sources = []
    for sid, label, blurb in SOURCE_META:
        if sid == "neuro":
            count = _neuro_count(daemon)
            present = daemon is not None
            path = "neuro-substrate"
        else:
            bucket = file_by_source[sid]
            count = len(bucket)
            present = count > 0
            path = {
                "grok": "~/.grok/memory-v2",
                "hermes": "~/.hermes/memories",
                "zoth-bot": "~/.config/zothos/zoth-bot/bots",
                "agy": "~/.gemini",
            }[sid]
        sources.append(
            {
                "id": sid,
                "label": label,
                "blurb": blurb,
                "count": count,
                "ok": present,
                "path": path,
            }
        )

    if wanted == "neuro":
        chosen = neuro_items
        chosen.sort(key=lambda it: float(it.get("mtime") or 0), reverse=True)
    elif wanted in file_by_source:
        chosen = [it for it in file_by_source[wanted] if _matches_query(it, q)]
        chosen.sort(key=lambda it: float(it.get("mtime") or 0), reverse=True)
    elif wanted:
        chosen = []
    else:
        files: List[Dict[str, Any]] = []
        for bucket in (grok_items, hermes_items, bot_items, agy_items):
            files.extend(it for it in bucket if _matches_query(it, q))
        files.sort(key=lambda it: float(it.get("mtime") or 0), reverse=True)
        chosen = files + neuro_items

    sliced = chosen[:cap]
    file_total = sum(len(file_by_source[k]) for k in file_by_source)
    return {
        "sources": sources,
        "items": sliced,
        "total": len(chosen),
        "shown": len(sliced),
        "limit": cap,
        "query": q,
        "source": wanted,
        "include_archive": bool(include_archive),
        "home": str(root),
        "mix_count": file_total + len(neuro_items),
        "file_count": file_total,
    }
