"""Tests for cross-platform compatibility utilities in neuro_memory_daemon.compat."""

from __future__ import annotations

import os
from pathlib import Path

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


def test_platform_detection_booleans():
    """Verify platform detection functions return boolean types."""
    assert isinstance(is_windows(), bool)
    assert isinstance(is_macos(), bool)
    assert isinstance(is_linux(), bool)
    assert isinstance(is_termux(), bool)


def test_normalize_path(temp_dir: Path):
    """Test path normalization across relative and absolute inputs."""
    rel_path = "subfolder/test_file.txt"
    norm = normalize_path(rel_path, base_dir=temp_dir)
    assert norm.is_absolute()
    assert str(norm).endswith("test_file.txt")

    abs_path = temp_dir / "already_abs.txt"
    norm_abs = normalize_path(abs_path)
    assert norm_abs == abs_path.resolve()


def test_ensure_dir(temp_dir: Path):
    """Test recursive directory creation."""
    target = temp_dir / "nested" / "deep" / "dir"
    assert not target.exists()
    ensured = ensure_dir(target)
    assert ensured.exists()
    assert ensured.is_dir()


def test_atomic_write_text(temp_dir: Path):
    """Test atomic text writing with utf-8 encoding."""
    target_file = temp_dir / "atomic_sample.txt"
    content = "🧠 Cognitive Neuro-Memory Substrate ⚡"
    
    written_path = atomic_write(target_file, content, encoding="utf-8")
    assert written_path.exists()
    assert written_path.read_text(encoding="utf-8") == content


def test_atomic_write_bytes(temp_dir: Path):
    """Test atomic binary data writing."""
    target_file = temp_dir / "atomic_sample.bin"
    raw_bytes = b"\x00\x01\x02\x03\xfe\xff"

    written_path = atomic_write(target_file, raw_bytes)
    assert written_path.exists()
    assert written_path.read_bytes() == raw_bytes


def test_atomic_replace(temp_dir: Path):
    """Test atomic replacement of an existing destination file."""
    src = temp_dir / "src.tmp"
    dst = temp_dir / "dst.txt"

    src.write_text("New content", encoding="utf-8")
    dst.write_text("Old content", encoding="utf-8")

    atomic_replace(src, dst)
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text(encoding="utf-8") == "New content"


def test_safe_read_and_write_text(temp_dir: Path):
    """Test safe read with encoding fallback."""
    file_path = temp_dir / "safe_text.txt"
    text = "Line 1\nLine 2 with special chars: äöü—✓"

    safe_write_text(file_path, text, atomic=True)
    read_back = safe_read_text(file_path)
    assert read_back == text


def test_safe_read_and_write_json(temp_dir: Path):
    """Test safe JSON reading and writing with default fallbacks."""
    json_path = temp_dir / "safe_data.json"
    data = {"name": "neuro-memory", "version": "0.1.0", "active": True, "count": 42}

    safe_write_json(json_path, data, indent=2, atomic=True)
    loaded = safe_read_json(json_path)
    assert loaded == data

    # Test non-existent file returns default
    missing = temp_dir / "non_existent.json"
    assert safe_read_json(missing, default={"fallback": True}) == {"fallback": True}

    # Test corrupt JSON returns default
    corrupt = temp_dir / "corrupt.json"
    corrupt.write_text("{invalid json:", encoding="utf-8")
    assert safe_read_json(corrupt, default=None) is None


def test_get_default_data_dir():
    """Verify application data directory determination and creation."""
    data_dir = get_default_data_dir("neuro_memory_test_app")
    assert isinstance(data_dir, Path)
    assert data_dir.exists()
    assert data_dir.is_dir()
    assert "neuro_memory_test_app" in str(data_dir)
