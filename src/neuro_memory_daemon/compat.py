"""Cross-platform compatibility utilities for neuro-memory-daemon.

Provides atomic file operations, safe path normalization (Linux, macOS, Windows,
Android/Termux), robust multi-encoding text I/O fallbacks, and platform detection.
All functions rely strictly on the Python standard library.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, List, Optional, Union


def is_windows() -> bool:
    """Return True if running on Windows."""
    return sys.platform.startswith("win") or platform.system() == "Windows"


def is_macos() -> bool:
    """Return True if running on macOS."""
    return sys.platform == "darwin" or platform.system() == "Darwin"


def is_linux() -> bool:
    """Return True if running on Linux (including Android/Termux)."""
    return sys.platform.startswith("linux") or platform.system() == "Linux"


def is_termux() -> bool:
    """Return True if running inside a Termux environment on Android."""
    if "TERMUX_VERSION" in os.environ or "TERMUX_APP_PID" in os.environ:
        return True
    prefix = os.environ.get("PREFIX", "")
    if "com.termux" in prefix:
        return True
    if os.path.exists("/data/data/com.termux"):
        return True
    return False


def normalize_path(
    path: Union[str, Path, os.PathLike],
    base_dir: Optional[Union[str, Path, os.PathLike]] = None,
) -> Path:
    """Normalize and resolve a path across Linux, macOS, Windows, and Termux.

    Expands user home directory (`~`), environment variables (`$VAR` or `%VAR%`),
    and resolves relative paths against `base_dir` (defaulting to cwd).

    Args:
        path: Path string or Path object to normalize.
        base_dir: Optional base directory to resolve relative paths against.

    Returns:
        Fully resolved absolute Path object.
    """
    raw_str = os.fspath(path)

    # Expand environment variables
    expanded_vars = os.path.expandvars(raw_str)

    # Handle Termux home directory expansion if ~ is used and HOME is overridden
    if is_termux() and expanded_vars.startswith("~"):
        termux_home = os.environ.get("HOME", "/data/data/com.termux/files/home")
        if expanded_vars == "~":
            expanded_vars = termux_home
        elif expanded_vars.startswith("~/"):
            expanded_vars = os.path.join(termux_home, expanded_vars[2:])

    # Standard user home expansion
    expanded_user = os.path.expanduser(expanded_vars)

    path_obj = Path(expanded_user)
    if not path_obj.is_absolute():
        base = Path(base_dir).resolve() if base_dir is not None else Path.cwd()
        path_obj = base / path_obj

    try:
        return path_obj.resolve()
    except (OSError, RuntimeError):
        # Fallback if resolve fails due to OS path constraints or symlink loops
        return path_obj.absolute()


def ensure_dir(path: Union[str, Path, os.PathLike]) -> Path:
    """Ensure a directory exists, creating parents if necessary.

    Args:
        path: Directory path to create.

    Returns:
        Resolved Path object of the ensured directory.
    """
    dir_path = normalize_path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def atomic_replace(
    src_path: Union[str, Path, os.PathLike],
    dst_path: Union[str, Path, os.PathLike],
    max_retries: int = 5,
    retry_delay: float = 0.05,
) -> None:
    """Atomically replace dst_path with src_path.

    On Windows, transient file locks (e.g. anti-virus, search indexing) can cause
    PermissionError or FileExistsError. This function retries with exponential backoff.

    Args:
        src_path: Source temporary file path.
        dst_path: Destination target file path.
        max_retries: Maximum retry attempts for transient locks.
        retry_delay: Initial delay in seconds between retries.
    """
    src = Path(src_path)
    dst = Path(dst_path)

    last_err: Optional[Exception] = None
    delay = retry_delay

    for attempt in range(max_retries):
        try:
            os.replace(src, dst)
            return
        except (PermissionError, OSError) as err:
            last_err = err
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                break

    if last_err is not None:
        raise last_err


def atomic_write(
    file_path: Union[str, Path, os.PathLike],
    content: Union[str, bytes],
    encoding: str = "utf-8",
    make_dirs: bool = True,
    sync: bool = True,
) -> Path:
    """Write content to a file atomically via a temporary file and atomic replace.

    Ensures that the destination file is never left in a partially written or
    corrupt state if the process or machine crashes during write.

    Args:
        file_path: Target destination path.
        content: String or bytes content to write.
        encoding: Text encoding when content is a string (default: utf-8).
        make_dirs: Whether to create parent directories automatically.
        sync: Whether to flush and fsync data to physical storage before rename.

    Returns:
        Path to the destination file.
    """
    dest = normalize_path(file_path)
    parent_dir = dest.parent

    if make_dirs:
        parent_dir.mkdir(parents=True, exist_ok=True)

    mode = "w" if isinstance(content, str) else "wb"
    file_encoding = encoding if isinstance(content, str) else None

    # Write to a temporary file in the same directory to guarantee same filesystem
    temp_file = tempfile.NamedTemporaryFile(
        mode=mode,
        dir=str(parent_dir),
        prefix=f".{dest.name}.tmp_",
        delete=False,
        encoding=file_encoding,
    )

    temp_path = Path(temp_file.name)
    try:
        with temp_file as f:
            f.write(content)
            f.flush()
            if sync:
                try:
                    os.fsync(f.fileno())
                except (OSError, AttributeError):
                    # Some filesystems or memory mounts do not support fsync
                    pass

        atomic_replace(temp_path, dest)
        return dest
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def safe_read_text(
    file_path: Union[str, Path, os.PathLike],
    fallback_encodings: Optional[List[str]] = None,
    errors: str = "replace",
) -> str:
    """Read text from a file with automatic fallback across common encodings.

    Attempts primary UTF-8 decoding, falling back to UTF-8-SIG, Latin-1, CP1252,
    and finally decoded with the specified error handler.

    Args:
        file_path: Path to the text file.
        fallback_encodings: List of candidate encodings to attempt.
        errors: Error handling scheme for decoding ('replace', 'ignore', 'strict').

    Returns:
        Decoded string content.
    """
    path = normalize_path(file_path)
    raw_bytes = path.read_bytes()

    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    if fallback_encodings:
        encodings = fallback_encodings + [e for e in encodings if e not in fallback_encodings]

    for enc in encodings:
        try:
            return raw_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue

    return raw_bytes.decode("utf-8", errors=errors)


def safe_write_text(
    file_path: Union[str, Path, os.PathLike],
    text: str,
    encoding: str = "utf-8",
    atomic: bool = True,
) -> Path:
    """Write text to a file safely.

    Args:
        file_path: Target destination path.
        text: String content to write.
        encoding: Text encoding (default: utf-8).
        atomic: If True, writes via atomic temporary file replacement.

    Returns:
        Path to the written file.
    """
    if atomic:
        return atomic_write(file_path, text, encoding=encoding)

    dest = normalize_path(file_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding=encoding) as f:
        f.write(text)
    return dest


def safe_read_json(
    file_path: Union[str, Path, os.PathLike],
    default: Any = None,
) -> Any:
    """Read and parse a JSON file with safe error handling and UTF-8 fallback.

    Args:
        file_path: Path to the JSON file.
        default: Default value returned if the file does not exist or is invalid JSON.

    Returns:
        Parsed JSON object (dict, list, etc.) or default value.
    """
    path = normalize_path(file_path)
    if not path.exists():
        return default

    try:
        content = safe_read_text(path)
        if not content.strip():
            return default
        return json.loads(content)
    except Exception:
        return default


def safe_write_json(
    file_path: Union[str, Path, os.PathLike],
    data: Any,
    indent: int = 2,
    atomic: bool = True,
) -> Path:
    """Serialize and write an object to a JSON file safely.

    Args:
        file_path: Target file path.
        data: Python object to serialize to JSON.
        indent: JSON indentation formatting.
        atomic: If True, uses atomic write.

    Returns:
        Path to the saved JSON file.
    """
    serialized = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    return safe_write_text(file_path, serialized, encoding="utf-8", atomic=atomic)


def get_default_data_dir(app_name: str = "neuro_memory_daemon") -> Path:
    """Determine the standard application data directory based on host platform.

    - Android/Termux: $HOME/.<app_name>
    - Windows: %APPDATA%/<app_name>
    - macOS: ~/Library/Application Support/<app_name>
    - Linux: $XDG_DATA_HOME/<app_name> or ~/.local/share/<app_name>

    Args:
        app_name: Name of the application directory.

    Returns:
        Path object pointing to the ensured data directory.
    """
    if is_termux():
        home = os.environ.get("HOME", "/data/data/com.termux/files/home")
        base = Path(home) / f".{app_name}"
    elif is_windows():
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) / app_name if appdata else Path.home() / "AppData" / "Roaming" / app_name
    elif is_macos():
        base = Path.home() / "Library" / "Application Support" / app_name
    else:
        # Standard Linux XDG specification
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            base = Path(xdg_data) / app_name
        else:
            base = Path.home() / ".local" / "share" / app_name

    return ensure_dir(base)
