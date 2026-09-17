"""Tests for command-line interface in neuro_memory_daemon.cli."""

from __future__ import annotations

import json
from pathlib import Path

from neuro_memory_daemon.cli import build_parser, main


def test_cli_parser_build():
    """Verify CLI parser builds with all subcommands."""
    parser = build_parser()
    assert parser is not None
    args = parser.parse_args(["--no-color", "stats"])
    assert args.command == "stats"
    assert args.no_color is True


def test_cli_no_command_returns_zero(capsys):
    """Verify running CLI with no args prints banner and returns 0."""
    ret = main([])
    assert ret == 0
    captured = capsys.readouterr()
    assert "NEURO-MEMORY DAEMON" in captured.out or "neuro-memory" in captured.out.lower()


def test_cli_store_and_recall(temp_dir: Path, capsys):
    """Test storing and recalling memory through CLI."""
    db_file = str(temp_dir / "cli_db.json")

    # Store
    ret_store = main([
        "--db-path", db_file,
        "--no-color",
        "store",
        "Configured Redis cache cluster for low-latency session caching",
        "-t", "redis,cache,performance",
        "-c", "semantic",
        "-i", "0.9",
    ])
    assert ret_store == 0
    capsys.readouterr()

    # Recall
    ret_recall = main([
        "--db-path", db_file,
        "--no-color",
        "recall",
        "redis caching session",
        "-k", "2",
    ])
    assert ret_recall == 0
    captured = capsys.readouterr()
    assert "Redis" in captured.out or "caching" in captured.out.lower()


def test_cli_search_json(temp_dir: Path, capsys):
    """Test searching with JSON output."""
    db_file = str(temp_dir / "cli_db.json")

    main(["--db-path", db_file, "store", "Memory Alpha", "-t", "alpha"])
    capsys.readouterr()  # Clear stdout from store

    ret = main(["--db-path", db_file, "search", "Alpha", "--json"])
    assert ret == 0

    captured = capsys.readouterr()
    parsed = json.loads(captured.out.strip())
    assert isinstance(parsed, list)
    assert len(parsed) >= 1
    assert "Alpha" in parsed[0]["text"]


def test_cli_graph(temp_dir: Path, capsys):
    """Test graph output in json, mermaid, and ascii formats."""
    db_file = str(temp_dir / "cli_db.json")

    main(["--db-path", db_file, "store", "Node 1", "-t", "graph1"])
    main(["--db-path", db_file, "store", "Node 2", "-t", "graph1,graph2"])
    capsys.readouterr()

    # Mermaid
    ret_m = main(["--db-path", db_file, "graph", "--format", "mermaid"])
    assert ret_m == 0
    captured_m = capsys.readouterr()
    assert "flowchart" in captured_m.out or "graph TD" in captured_m.out

    # JSON
    ret_j = main(["--db-path", db_file, "graph", "--json"])
    assert ret_j == 0
    captured_j = capsys.readouterr()
    parsed_j = json.loads(captured_j.out.strip())
    assert "nodes" in parsed_j


def test_cli_consolidate_and_stats(temp_dir: Path, capsys):
    """Test consolidate and stats subcommands."""
    db_file = str(temp_dir / "cli_db.json")
    main(["--db-path", db_file, "store", "Temporary item", "-t", "temp"])
    capsys.readouterr()

    ret_cons = main(["--db-path", db_file, "consolidate", "--json"])
    assert ret_cons == 0
    captured_c = capsys.readouterr()
    parsed_c = json.loads(captured_c.out.strip())
    assert "nodes_processed" in parsed_c

    ret_stats = main(["--db-path", db_file, "stats", "--detailed", "--json"])
    assert ret_stats == 0
    captured_s = capsys.readouterr()
    parsed_s = json.loads(captured_s.out.strip())
    assert "total_memories" in parsed_s


def test_cli_doctor(temp_dir: Path, capsys):
    """Test diagnostics / doctor subcommand."""
    db_file = str(temp_dir / "cli_db.json")
    ret = main(["--db-path", db_file, "doctor", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out.strip())
    assert parsed.get("status") == "healthy"


def test_cli_internal_self_test(capsys):
    """Verify internal self-test runner passes."""
    ret = main(["--no-color", "test"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "passed successfully" in captured.out
