"""
neuro_memory_daemon.cli
~~~~~~~~~~~~~~~~~~~~~~~
Multi-OS Command-Line Interface and Protocol Hub for neuro-memory-daemon.
Pure Python standard library implementation (zero external dependencies).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from . import (
        MemoryDaemon,
        __version__,
        consolidate_memories,
        get_default_daemon,
        get_memory_graph,
        recall_memory,
        search_memories,
        store_memory,
    )
    from .mcp_server import run_mcp_server
except ImportError:
    from neuro_memory_daemon import (
        MemoryDaemon,
        __version__,
        consolidate_memories,
        get_default_daemon,
        get_memory_graph,
        recall_memory,
        search_memories,
        store_memory,
    )
    from neuro_memory_daemon.mcp_server import run_mcp_server

# ---------------------------------------------------------------------------
# Terminal Styling & Color Support
# ---------------------------------------------------------------------------

class Color:
    """ANSI color codes with automatic NO_COLOR and TTY detection."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

_COLOR_ENABLED = True

def _init_colors(no_color: bool = False) -> None:
    """Configure terminal color output state."""
    global _COLOR_ENABLED
    if no_color or "NO_COLOR" in os.environ or not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        _COLOR_ENABLED = False
    else:
        _COLOR_ENABLED = True
        # Enable ANSI support on Windows if possible
        if platform.system() == "Windows":
            os.system("")

def c(text: str, color_code: str) -> str:
    """Apply ANSI styling if colors are enabled."""
    if not _COLOR_ENABLED:
        return str(text)
    return f"{color_code}{text}{Color.RESET}"


def print_banner() -> None:
    """Print the Neuro-Memory Daemon CLI banner."""
    if not _COLOR_ENABLED:
        print(f"=== Neuro-Memory Daemon v{__version__} ===")
        return
    banner = f"""
{Color.BRIGHT_CYAN} 🧠 NEURO-MEMORY DAEMON {Color.DIM}v{__version__}{Color.RESET}
{Color.DIM}    Associative Cognitive Substrate & MCP Protocol Bridge{Color.RESET}
"""
    print(banner)


# ---------------------------------------------------------------------------
# CLI Command Handlers
# ---------------------------------------------------------------------------

def handle_store(args: argparse.Namespace) -> int:
    """Handle `store` subcommand."""
    text = args.text
    if text == "-" or not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print(c("Error: Memory text is required.", Color.BRIGHT_RED), file=sys.stderr)
            return 1

    tags = []
    if args.tags:
        for t in args.tags:
            tags.extend([tag.strip() for tag in t.split(",") if tag.strip()])

    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            print(c(f"Error parsing --metadata JSON: {e}", Color.BRIGHT_RED), file=sys.stderr)
            return 1

    daemon = get_default_daemon(db_path=args.db_path)
    res = daemon.store(
        text=text,
        tags=tags,
        importance=args.importance,
        category=args.category,
        perspective=args.perspective,
        agent_id=args.agent_id,
        metadata=metadata,
    )

    if args.json:
        print(json.dumps(res, indent=2))
        return 0

    print(c("✔ Memory Stored Successfully", Color.BRIGHT_GREEN + Color.BOLD))
    print(f"  {c('ID:', Color.DIM)} {res['id']}")
    print(f"  {c('Category:', Color.CYAN)} {res['category']}  {c('Importance:', Color.YELLOW)} {res['importance']}")
    if res['tags']:
        print(f"  {c('Tags:', Color.MAGENTA)} {', '.join(res['tags'])}")
    print(f"  {c('Synapses Formed:', Color.BLUE)} {res['synaptic_links_formed']}")
    print(f"  {c('Content:', Color.DIM)} {res['text']}")
    return 0


def handle_recall(args: argparse.Namespace) -> int:
    """Handle `recall` subcommand."""
    query = args.query
    if query == "-" or not query:
        if not sys.stdin.isatty():
            query = sys.stdin.read().strip()
        else:
            print(c("Error: Retrieval query is required.", Color.BRIGHT_RED), file=sys.stderr)
            return 1

    daemon = get_default_daemon(db_path=args.db_path)
    results = daemon.recall(
        query=query,
        top_k=args.top_k,
        min_score=args.min_score,
        category=args.category,
        spread_hops=args.spread_hops,
    )

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    print(c(f"🔍 Associative Recall for: '{query}'", Color.BRIGHT_CYAN + Color.BOLD))
    if not results:
        print(c("  No memories matched the retrieval cue above the threshold.", Color.DIM))
        return 0

    print(f"  Retrieved {len(results)} associative memories:\n")
    for i, r in enumerate(results, 1):
        score_pct = int(r["score"] * 100)
        score_color = Color.BRIGHT_GREEN if score_pct >= 60 else Color.BRIGHT_YELLOW
        cat_str = f"({r['category']})"
        print(f"  {c(f'[{i}]', Color.BOLD)} {c(f'{score_pct}% resonance', score_color)} {c(cat_str, Color.CYAN)} - {r['id'][:8]}")
        print(f"      {r['text']}")
        if r["tags"]:
            print(f"      {c('Tags:', Color.DIM)} {c(', '.join(r['tags']), Color.MAGENTA)}")
        print(f"      {c('Synapses:', Color.DIM)} {r['connected_synapses']} | {c('Accesses:', Color.DIM)} {r['access_count']}\n")

    return 0


def handle_search(args: argparse.Namespace) -> int:
    """Handle `search` subcommand."""
    tags = []
    if args.tag:
        for t in args.tag:
            tags.extend([tag.strip() for tag in t.split(",") if tag.strip()])

    daemon = get_default_daemon(db_path=args.db_path)
    results = daemon.search(
        query=args.query or "",
        tags=tags if tags else None,
        category=args.category,
        limit=args.limit,
        agent_id=args.agent_id,
    )

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    print(c(f"🔎 Memory Search ({len(results)} matches)", Color.BRIGHT_CYAN + Color.BOLD))
    for i, r in enumerate(results, 1):
        print(f"  {c(f'{i}.', Color.BOLD)} [{c(r['category'], Color.CYAN)}] {r['text'][:80]}")
        if r["tags"]:
            print(f"     {c('Tags:', Color.DIM)} {c(', '.join(r['tags']), Color.MAGENTA)}")
    return 0


def handle_graph(args: argparse.Namespace) -> int:
    """Handle `graph` subcommand."""
    fmt = args.format
    if args.json:
        fmt = "json"

    daemon = get_default_daemon(db_path=args.db_path)
    graph_out = daemon.get_graph(
        format=fmt,
        min_weight=args.min_weight,
        node_limit=args.node_limit,
        root_id=args.root_id,
    )

    if isinstance(graph_out, dict):
        print(json.dumps(graph_out, indent=2))
    else:
        print(graph_out)
    return 0


def handle_consolidate(args: argparse.Namespace) -> int:
    """Handle `consolidate` subcommand."""
    daemon = get_default_daemon(db_path=args.db_path)
    res = daemon.consolidate(
        decay_rate=args.decay_rate,
        prune_threshold=args.prune_threshold,
        stdp_window=args.stdp_window,
    )

    if args.json:
        print(json.dumps(res, indent=2))
        return 0

    print(c("✨ Memory Consolidation Complete (Sleep Cycle)", Color.BRIGHT_MAGENTA + Color.BOLD))
    print(f"  {c('Nodes Processed:', Color.DIM)} {res['nodes_processed']}")
    print(f"  {c('Decayed Nodes:', Color.YELLOW)} {res['decayed_nodes']}")
    print(f"  {c('Strengthened Synapses (STDP):', Color.BRIGHT_GREEN)} {res['strengthened_synapses']}")
    print(f"  {c('Pruned Synapses:', Color.RED)} {res['pruned_synapses']}")
    print(f"  {c('Pruned Ephemeral Nodes:', Color.RED)} {res['pruned_nodes']}")
    print(f"  {c('Remaining Nodes:', Color.CYAN)} {res['remaining_nodes']}")
    print(f"  {c('Duration:', Color.DIM)} {res['duration_seconds']}s")
    return 0


def handle_stats(args: argparse.Namespace) -> int:
    """Handle `stats` subcommand."""
    daemon = get_default_daemon(db_path=args.db_path)
    stats = daemon.get_stats(detailed=args.detailed)

    if args.json:
        print(json.dumps(stats, indent=2))
        return 0

    print(c("📊 Memory Substrate Telemetry", Color.BRIGHT_CYAN + Color.BOLD))
    print(f"  ┌──────────────────────────────┬──────────────────┐")
    print(f"  │ {c('Metric', Color.BOLD):<28} │ {c('Value', Color.BOLD):<16} │")
    print(f"  ├──────────────────────────────┼──────────────────┤")
    print(f"  │ Total Memories               │ {stats['total_memories']:<16} │")
    print(f"  │ Total Synaptic Edges         │ {stats['total_synapses']:<16} │")
    print(f"  │ Synaptic Density (edges/node)│ {stats['synaptic_density']:<16} │")
    print(f"  │ Working Memory Slots         │ {stats['working_memory_usage']:<16} │")
    print(f"  │ Average Importance           │ {stats['average_importance']:<16} │")
    print(f"  │ Average Accesses per Node    │ {stats['average_accesses']:<16} │")
    print(f"  └──────────────────────────────┴──────────────────┘")

    if stats.get("categories"):
        print(c("\n  Categories Breakdown:", Color.BOLD))
        for cat, cnt in stats["categories"].items():
            print(f"    • {c(cat, Color.CYAN)}: {cnt}")

    if stats.get("top_tags"):
        print(c("\n  Top Tags:", Color.BOLD))
        tag_items = [f"{t} ({cnt})" for t, cnt in stats["top_tags"].items()]
        print(f"    {c(', '.join(tag_items), Color.MAGENTA)}")

    return 0


def handle_diagnostics(args: argparse.Namespace) -> int:
    """Handle `platform` / `doctor` / `diagnostics` subcommand."""
    daemon = get_default_daemon(db_path=args.db_path)
    diag = daemon.diagnostics(verbose=args.verbose)

    if args.json:
        print(json.dumps(diag, indent=2))
        return 0

    print(c("🩺 Neuro-Memory Substrate Doctor & Diagnostics", Color.BRIGHT_GREEN + Color.BOLD))
    print(f"  Substrate Health:   {c('HEALTHY (Operational)', Color.BRIGHT_GREEN)}")
    print(f"  Daemon Version:     {diag['version']}")
    print(f"  Storage DB Path:    {diag['db_path']}")
    print(f"  Database Exists:    {'Yes' if diag['db_exists'] else 'No (Fresh In-Memory/Pending)'}")
    print(f"  DB Size on Disk:    {diag['db_size_bytes']} bytes")
    print(f"  Total Memory Nodes: {diag['nodes_count']}")
    print(f"  OS / Platform:      {diag['system']} ({diag['machine']})")
    print(f"  Python Runtime:     v{diag['python_version']}")
    print(f"  Uptime:             {diag['uptime_seconds']}s")

    if args.verbose and "synapse_weights_distribution" in diag:
        print(c("\n  Synapse Distribution:", Color.BOLD))
        for k, v in diag["synapse_weights_distribution"].items():
            print(f"    • {k}: {v}")

    return 0


def handle_mcp(args: argparse.Namespace) -> int:
    """Handle `mcp` subcommand (Stdio Model Context Protocol server)."""
    run_mcp_server(db_path=args.db_path)
    return 0


# ---------------------------------------------------------------------------
# Web UI Server Handler (Material 3 Memory Studio)
# ---------------------------------------------------------------------------

_STUDIO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Neuro-Memory Studio | Google Material 3 Substrate</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --md-sys-color-primary: #a8c7fa;
      --md-sys-color-on-primary: #062e6f;
      --md-sys-color-primary-container: #0842a0;
      --md-sys-color-on-primary-container: #d3e3fd;
      --md-sys-color-surface: #111318;
      --md-sys-color-surface-container: #1e1f25;
      --md-sys-color-surface-container-high: #282a30;
      --md-sys-color-on-surface: #e2e2e9;
      --md-sys-color-on-surface-variant: #c4c6d0;
      --md-sys-color-outline: #8e9099;
      --md-sys-color-secondary: #7fcfff;
      --md-sys-color-tertiary: #c5c0ff;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--md-sys-color-surface);
      color: var(--md-sys-color-on-surface);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: var(--md-sys-color-surface-container);
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 20px;
      font-weight: 700;
      color: var(--md-sys-color-primary);
    }
    .badge {
      background: var(--md-sys-color-primary-container);
      color: var(--md-sys-color-on-primary-container);
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 12px;
      font-weight: 500;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      flex: 1;
      gap: 20px;
      padding: 20px;
    }
    .panel {
      background: var(--md-sys-color-surface-container);
      border-radius: 16px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      border: 1px solid rgba(255,255,255,0.05);
    }
    h2 { font-size: 16px; font-weight: 600; color: var(--md-sys-color-on-surface); }
    input, textarea, select, button {
      font-family: inherit;
      border-radius: 8px;
      border: 1px solid var(--md-sys-color-outline);
      background: var(--md-sys-color-surface-container-high);
      color: #fff;
      padding: 10px 12px;
      font-size: 14px;
    }
    textarea { resize: vertical; min-height: 80px; }
    button {
      background: var(--md-sys-color-primary);
      color: var(--md-sys-color-on-primary);
      border: none;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
    }
    button:hover { opacity: 0.9; }
    .btn-secondary {
      background: var(--md-sys-color-surface-container-high);
      color: var(--md-sys-color-primary);
      border: 1px solid rgba(255,255,255,0.1);
    }
    .stats-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }
    .stat-card {
      background: var(--md-sys-color-surface-container-high);
      padding: 14px;
      border-radius: 12px;
      text-align: center;
    }
    .stat-val { font-size: 24px; font-weight: 700; color: var(--md-sys-color-primary); }
    .stat-lbl { font-size: 12px; color: var(--md-sys-color-on-surface-variant); margin-top: 4px; }
    .memory-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      overflow-y: auto;
      max-height: 500px;
    }
    .memory-card {
      background: var(--md-sys-color-surface-container-high);
      padding: 14px;
      border-radius: 12px;
      border-left: 4px solid var(--md-sys-color-primary);
    }
    .memory-meta {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--md-sys-color-on-surface-variant);
      margin-bottom: 6px;
    }
    .tags-list { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
    .tag-chip {
      background: rgba(168,199,250,0.15);
      color: var(--md-sys-color-primary);
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
    }
    pre {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      background: #000;
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      color: #a8c7fa;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>🧠 Neuro-Memory Studio</span>
      <span class="badge">Google Material 3</span>
    </div>
    <div style="display:flex; gap:10px;">
      <button class="btn-secondary" onclick="triggerConsolidation()">⚡ Consolidate</button>
      <button onclick="refreshData()">🔄 Refresh</button>
    </div>
  </header>

  <div class="main-grid">
    <div class="panel">
      <h2>Store Memory</h2>
      <textarea id="storeText" placeholder="Enter memory text, observation, or fact..."></textarea>
      <input type="text" id="storeTags" placeholder="Tags (comma separated, e.g. code, bug, ui)">
      <div style="display:flex; gap:8px;">
        <select id="storeCategory" style="flex:1;">
          <option value="episodic">Episodic</option>
          <option value="semantic">Semantic</option>
          <option value="procedural">Procedural</option>
          <option value="working">Working</option>
        </select>
        <input type="number" id="storeImportance" value="0.5" step="0.1" min="0" max="1" style="width:70px;" title="Importance">
      </div>
      <button onclick="submitStore()">Store in Substrate</button>

      <hr style="border-color:rgba(255,255,255,0.05); margin: 8px 0;">

      <h2>Associative Recall</h2>
      <input type="text" id="recallQuery" placeholder="Query cue (e.g. design system)...">
      <button class="btn-secondary" onclick="submitRecall()">Pattern Completion Recall</button>

      <div id="recallResults" style="display:none; flex-direction:column; gap:8px;">
        <h3 style="font-size:13px; color:var(--md-sys-color-secondary);">Recall Resonance:</h3>
        <div id="recallContainer" class="memory-list" style="max-height:220px;"></div>
      </div>
    </div>

    <div class="panel">
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-val" id="statNodes">0</div>
          <div class="stat-lbl">Total Memories</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="statSynapses">0</div>
          <div class="stat-lbl">Synaptic Edges</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="statDensity">0.0</div>
          <div class="stat-lbl">Synaptic Density</div>
        </div>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h2>Synaptic Memory Substrate</h2>
        <div style="display:flex; gap:8px;">
          <button class="btn-secondary" style="font-size:12px; padding:6px 10px;" onclick="viewGraph('mermaid')">Mermaid</button>
          <button class="btn-secondary" style="font-size:12px; padding:6px 10px;" onclick="viewGraph('json')">Graph JSON</button>
        </div>
      </div>

      <div id="graphView" style="display:none;">
        <pre id="graphContent"></pre>
      </div>

      <div id="memoryContainer" class="memory-list">
        <!-- Rendered dynamically -->
      </div>
    </div>
  </div>

  <script>
    async function api(path, method='GET', body=null) {
      const opts = { method, headers: { 'Content-Type': 'application/json' } };
      if (body) opts.body = JSON.stringify(body);
      const res = await fetch(path, opts);
      return res.json();
    }

    async function refreshData() {
      const stats = await api('/api/stats');
      document.getElementById('statNodes').innerText = stats.total_memories || 0;
      document.getElementById('statSynapses').innerText = stats.total_synapses || 0;
      document.getElementById('statDensity').innerText = stats.synaptic_density || '0.0';

      const memories = await api('/api/memories');
      const container = document.getElementById('memoryContainer');
      container.innerHTML = '';
      if (!memories || memories.length === 0) {
        container.innerHTML = '<div style="color:var(--md-sys-color-on-surface-variant); text-align:center; padding:30px;">Substrate is empty. Store your first memory!</div>';
        return;
      }
      memories.forEach(m => {
        const card = document.createElement('div');
        card.className = 'memory-card';
        card.innerHTML = `
          <div class="memory-meta">
            <span>[${m.category.toUpperCase()}] • ID: ${m.id.substring(0,8)}</span>
            <span>Imp: ${m.importance} • Access: ${m.access_count}</span>
          </div>
          <div>${m.text}</div>
          <div class="tags-list">
            ${(m.tags || []).map(t => `<span class="tag-chip">#${t}</span>`).join('')}
          </div>
        `;
        container.appendChild(card);
      });
    }

    async function submitStore() {
      const text = document.getElementById('storeText').value.trim();
      if (!text) return alert('Please enter memory text');
      const tagsStr = document.getElementById('storeTags').value;
      const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];
      const category = document.getElementById('storeCategory').value;
      const importance = parseFloat(document.getElementById('storeImportance').value || 0.5);

      await api('/api/store', 'POST', { text, tags, category, importance });
      document.getElementById('storeText').value = '';
      document.getElementById('storeTags').value = '';
      refreshData();
    }

    async function submitRecall() {
      const query = document.getElementById('recallQuery').value.trim();
      if (!query) return;
      const results = await api('/api/recall', 'POST', { query, top_k: 5 });
      const wrap = document.getElementById('recallResults');
      const container = document.getElementById('recallContainer');
      wrap.style.display = 'flex';
      container.innerHTML = '';
      if (!results || results.length === 0) {
        container.innerHTML = '<div style="font-size:12px; color:#888;">No associative matches found.</div>';
        return;
      }
      results.forEach(r => {
        const item = document.createElement('div');
        item.className = 'memory-card';
        item.style.borderLeftColor = '#7fcfff';
        item.innerHTML = `
          <div class="memory-meta">
            <span>${Math.round(r.score*100)}% Resonance • [${r.category}]</span>
          </div>
          <div style="font-size:13px;">${r.text}</div>
        `;
        container.appendChild(item);
      });
    }

    async function triggerConsolidation() {
      const res = await api('/api/consolidate', 'POST', {});
      alert(`Consolidation Complete!\\nDecayed: ${res.decayed_nodes}\\nStrengthened: ${res.strengthened_synapses}\\nPruned Synapses: ${res.pruned_synapses}`);
      refreshData();
    }

    async function viewGraph(fmt) {
      const gView = document.getElementById('graphView');
      const gContent = document.getElementById('graphContent');
      if (gView.style.display === 'block') {
        gView.style.display = 'none';
        return;
      }
      const data = await api('/api/graph?format=' + fmt);
      gContent.innerText = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
      gView.style.display = 'block';
    }

    window.onload = refreshData;
  </script>
</body>
</html>
"""

class MemoryStudioHTTPHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler for Material 3 Memory Studio Web UI."""

    daemon: MemoryDaemon

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(_STUDIO_HTML.encode("utf-8"))
            return

        if path == "/api/stats":
            stats = self.daemon.get_stats(detailed=True)
            self._send_json(stats)
            return

        if path == "/api/diagnostics":
            diag = self.daemon.diagnostics(verbose=True)
            self._send_json(diag)
            return

        if path == "/api/memories":
            nodes = [n.to_dict() for n in self.daemon.nodes.values()]
            nodes.sort(key=lambda x: x["created_at"], reverse=True)
            self._send_json(nodes)
            return

        if path == "/api/graph":
            query_params = urllib.parse.parse_qs(parsed.query)
            fmt = query_params.get("format", ["json"])[0]
            graph = self.daemon.get_graph(format=fmt)
            if isinstance(graph, dict):
                self._send_json(graph)
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(str(graph).encode("utf-8"))
            return

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if path == "/api/store":
            res = self.daemon.store(
                text=data.get("text", ""),
                tags=data.get("tags"),
                importance=float(data.get("importance", 0.5)),
                category=data.get("category", "episodic"),
                perspective=data.get("perspective", "first_person"),
                agent_id=data.get("agent_id", "default"),
                metadata=data.get("metadata"),
            )
            self._send_json(res)
            return

        if path == "/api/recall":
            results = self.daemon.recall(
                query=data.get("query", ""),
                top_k=int(data.get("top_k", 5)),
                min_score=float(data.get("min_score", 0.1)),
                category=data.get("category"),
                spread_hops=int(data.get("spread_hops", 2)),
            )
            self._send_json(results)
            return

        if path == "/api/search":
            results = self.daemon.search(
                query=data.get("query", ""),
                tags=data.get("tags"),
                category=data.get("category"),
                limit=int(data.get("limit", 10)),
                agent_id=data.get("agent_id"),
            )
            self._send_json(results)
            return

        if path == "/api/consolidate":
            res = self.daemon.consolidate(
                decay_rate=float(data.get("decay_rate", 0.05)),
                prune_threshold=float(data.get("prune_threshold", 0.05)),
                stdp_window=float(data.get("stdp_window", 3600.0)),
            )
            self._send_json(res)
            return

        self.send_error(404, "Not Found")

    def _send_json(self, data: Any) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard access logs to keep CLI clean."""
        pass


def handle_serve(args: argparse.Namespace) -> int:
    """Handle `serve` subcommand: Launch Google Material 3 Memory Studio Web UI."""
    host = args.host
    port = args.port
    daemon = get_default_daemon(db_path=args.db_path)

    # Check if UI server was implemented in ui_server or other modules
    try:
        from .ui_server import run_server as ui_serve  # type: ignore
        return ui_serve(host=host, port=port, open_browser=args.open_browser, daemon=daemon)
    except (ImportError, AttributeError):
        pass

    try:
        from .web_ui import run_server as custom_serve  # type: ignore
        return custom_serve(host=host, port=port, daemon=daemon)
    except (ImportError, AttributeError):
        pass

    try:
        from .server import run_server as custom_serve2  # type: ignore
        return custom_serve2(host=host, port=port, daemon=daemon)
    except (ImportError, AttributeError):
        pass

    # Standard built-in HTTP server
    handler_class = MemoryStudioHTTPHandler
    handler_class.daemon = daemon

    server = HTTPServer((host, port), handler_class)
    url = f"http://{host}:{port}"
    print(c("🚀 Google Material 3 Memory Studio Running", Color.BRIGHT_GREEN + Color.BOLD))
    print(f"  {c('Local URL:', Color.CYAN)} {c(url, Color.UNDERLINE)}")
    print(f"  {c('Storage:', Color.DIM)} {daemon.db_path}")
    print(f"  {c('Press Ctrl+C to stop the server.', Color.DIM)}")

    if args.open_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(c("\nStopping Memory Studio server.", Color.YELLOW))
        server.server_close()
    return 0


# ---------------------------------------------------------------------------
# Internal Self-Verification Test Runner
# ---------------------------------------------------------------------------

def handle_test(args: argparse.Namespace) -> int:
    """Execute internal self-verification test suite."""
    import tempfile
    print(c("🧪 Running Neuro-Memory Internal Self-Verification Suite...", Color.BRIGHT_CYAN + Color.BOLD))
    
    start_ts = time.time()
    passed = 0
    failed = 0
    tests = []

    def run_unit(name: str, fn: Any) -> None:
        nonlocal passed, failed
        t0 = time.time()
        try:
            fn()
            dt = round((time.time() - t0) * 1000, 2)
            tests.append((name, True, f"{dt}ms", None))
            passed += 1
        except Exception as e:
            dt = round((time.time() - t0) * 1000, 2)
            tests.append((name, False, f"{dt}ms", str(e)))
            failed += 1

    # Test 1: Store & Synaptic Formation
    def test_store():
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "test.json"
            d = MemoryDaemon(db_path=db)
            m1 = d.store("User prefers dark theme in UI", tags=["ui", "theme", "preference"], category="episodic")
            m2 = d.store("Dark theme reduces eye strain", tags=["ui", "health", "theme"], category="semantic")
            assert len(d.nodes) == 2
            assert m1["id"] in d.nodes
            assert m2["id"] in d.nodes[m1["id"]].synapses or m1["id"] in d.nodes[m2["id"]].synapses
    run_unit("Memory Storage & Synapse Formation", test_store)

    # Test 2: Associative Pattern Completion Recall
    def test_recall():
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "test.json"
            d = MemoryDaemon(db_path=db)
            d.store("Neural networks use backpropagation gradient descent", tags=["ml", "ai"])
            d.store("Database indexes speed up B-Tree lookups", tags=["db", "sql"])
            recalled = d.recall("gradient descent backprop", top_k=2)
            assert len(recalled) >= 1
            assert "backpropagation" in recalled[0]["text"]
    run_unit("Associative Recall & Spreading Activation", test_recall)

    # Test 3: Filtered Full-Text Search
    def test_search():
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "test.json"
            d = MemoryDaemon(db_path=db)
            d.store("Quantum computing utilizes qubits and superposition", tags=["quantum", "physics"])
            d.store("Classical computers use binary transistors", tags=["classical", "hardware"])
            matches = d.search("qubits", tags=["quantum"])
            assert len(matches) == 1
            assert "Quantum" in matches[0]["text"]
    run_unit("Full-Text & Tag Filtered Search", test_search)

    # Test 4: Graph Formats (JSON, Mermaid, ASCII, DOT)
    def test_graph():
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "test.json"
            d = MemoryDaemon(db_path=db)
            d.store("Node Alpha", tags=["test"])
            d.store("Node Beta related to Alpha", tags=["test"])
            g_json = d.get_graph(format="json")
            assert "nodes" in g_json and "edges" in g_json
            g_mermaid = d.get_graph(format="mermaid")
            assert "graph TD" in g_mermaid
            g_ascii = d.get_graph(format="ascii")
            assert "Synaptic Memory Substrate" in g_ascii
            g_dot = d.get_graph(format="dot")
            assert "digraph MemorySubstrate" in g_dot
    run_unit("Synaptic Graph Multi-Format Generation", test_graph)

    # Test 5: Consolidation & STDP
    def test_consolidation():
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "test.json"
            d = MemoryDaemon(db_path=db)
            d.store("Ephemeral note", tags=["temp"], category="working", importance=0.01)
            d.store("Core knowledge", tags=["core"], category="semantic", importance=0.9)
            res = d.consolidate(decay_rate=0.5, prune_threshold=0.05)
            assert res["nodes_processed"] == 2
    run_unit("Sleep Consolidation & STDP Plasticity", test_consolidation)

    # Test 6: MCP JSON-RPC Server Handshake
    def test_mcp_server():
        from .mcp_server import MCPServer
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "test.json"
            server = MCPServer(db_path=str(db))
            # Test initialize
            init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
            resp = server.handle_request(init_req)
            assert resp and resp["result"]["protocolVersion"] == "2024-11-05"

            # Test tools/list
            tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            tools_resp = server.handle_request(tools_req)
            tool_names = [t["name"] for t in tools_resp["result"]["tools"]]
            assert "memory_store" in tool_names
            assert "memory_recall" in tool_names

            # Test tools/call memory_store
            call_req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "memory_store", "arguments": {"text": "MCP test memory", "tags": ["mcp"]}},
            }
            call_resp = server.handle_request(call_req)
            assert call_resp and not call_resp["result"]["isError"]
    run_unit("MCP JSON-RPC 2.0 Protocol Handshake & Tools", test_mcp_server)

    # Render results table
    print("\n  ┌──────────────────────────────────────────┬──────────┬───────────┐")
    print(f"  │ {c('Test Suite Component', Color.BOLD):<40} │ {c('Status', Color.BOLD):<8} │ {c('Duration', Color.BOLD):<9} │")
    print("  ├──────────────────────────────────────────┼──────────┼───────────┤")
    for name, ok, duration, err in tests:
        status_str = c("PASSED", Color.BRIGHT_GREEN) if ok else c("FAILED", Color.BRIGHT_RED)
        print(f"  │ {name:<40} │ {status_str:<17} │ {duration:<9} │")
        if err:
            print(f"  │   └─ {c(err, Color.RED)}")
    print("  └──────────────────────────────────────────┴──────────┴───────────┘")

    total_time = round((time.time() - start_ts) * 1000, 2)
    if failed == 0:
        print(c(f"\n✔ All {passed} tests passed successfully in {total_time}ms.", Color.BRIGHT_GREEN + Color.BOLD))
        return 0
    else:
        print(c(f"\n❌ {failed} tests failed out of {passed + failed} total tests.", Color.BRIGHT_RED + Color.BOLD))
        return 1


# ---------------------------------------------------------------------------
# CLI Main Parser & Entrypoint
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line interface parser."""
    parser = argparse.ArgumentParser(
        prog="neuro-memory",
        description="🧠 Neuro-Memory Daemon: Cognitive Associative Substrate & MCP Protocol Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"neuro-memory-daemon v{__version__}",
        help="Show package version and exit.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colored output.",
    )
    parser.add_argument(
        "--db-path", "--storage-path",
        type=str,
        default=None,
        help="Custom file path for the memory substrate database (default: ~/.neuro_memory/substrate.json).",
    )

    subparsers = parser.add_subparsers(dest="command", title="Commands", metavar="<command>")

    # 1. store
    p_store = subparsers.add_parser("store", help="Store a memory in the neural substrate.")
    p_store.add_argument("text", nargs="?", default="", help="Memory content to store (or pass '-' to read from stdin).")
    p_store.add_argument("-t", "--tags", action="append", help="Tags/keywords (e.g. -t tag1 -t tag2 or -t 'tag1,tag2').")
    p_store.add_argument("-c", "--category", default="episodic", choices=["episodic", "semantic", "procedural", "working"], help="Category.")
    p_store.add_argument("-i", "--importance", type=float, default=0.5, help="Importance score between 0.0 and 1.0 (default: 0.5).")
    p_store.add_argument("-p", "--perspective", default="first_person", help="Perspective (default: first_person).")
    p_store.add_argument("-a", "--agent-id", default="default", help="Agent identifier.")
    p_store.add_argument("-m", "--metadata", type=str, default=None, help="JSON string of custom metadata.")
    p_store.add_argument("--json", action="store_true", help="Output raw JSON response.")

    # 2. recall
    p_recall = subparsers.add_parser("recall", help="Associative pattern completion recall.")
    p_recall.add_argument("query", nargs="?", default="", help="Query cue prompt.")
    p_recall.add_argument("-k", "--top-k", type=int, default=5, help="Maximum number of memories to recall (default: 5).")
    p_recall.add_argument("-s", "--min-score", type=float, default=0.1, help="Minimum resonance score (default: 0.1).")
    p_recall.add_argument("-c", "--category", default=None, help="Filter by category.")
    p_recall.add_argument("-H", "--spread-hops", type=int, default=2, help="Synaptic spreading activation hops (default: 2).")
    p_recall.add_argument("--json", action="store_true", help="Output raw JSON response.")

    # 3. search
    p_search = subparsers.add_parser("search", help="Full-text and tag filtered search.")
    p_search.add_argument("query", nargs="?", default="", help="Search query string.")
    p_search.add_argument("-t", "--tag", action="append", help="Filter by tag.")
    p_search.add_argument("-c", "--category", default=None, help="Filter by category.")
    p_search.add_argument("-l", "--limit", type=int, default=10, help="Maximum search results (default: 10).")
    p_search.add_argument("-a", "--agent-id", default=None, help="Filter by agent ID.")
    p_search.add_argument("--json", action="store_true", help="Output raw JSON response.")

    # 4. graph
    p_graph = subparsers.add_parser("graph", help="Display synaptic graph relationships.")
    p_graph.add_argument("-f", "--format", choices=["json", "mermaid", "ascii", "dot"], default="ascii", help="Graph output format (default: ascii).")
    p_graph.add_argument("-w", "--min-weight", type=float, default=0.1, help="Minimum synaptic weight (default: 0.1).")
    p_graph.add_argument("-l", "--node-limit", type=int, default=50, help="Maximum nodes (default: 50).")
    p_graph.add_argument("-r", "--root-id", default=None, help="Focus root ID for local ego-graph.")
    p_graph.add_argument("--json", action="store_true", help="Output as JSON.")

    # 5. consolidate
    p_cons = subparsers.add_parser("consolidate", help="Trigger sleep/consolidation pass (apply STDP, decay, and prune).")
    p_cons.add_argument("-d", "--decay-rate", type=float, default=0.05, help="Decay rate multiplier (default: 0.05).")
    p_cons.add_argument("-p", "--prune-threshold", type=float, default=0.05, help="Synaptic pruning threshold (default: 0.05).")
    p_cons.add_argument("-w", "--stdp-window", type=float, default=3600.0, help="STDP window in seconds (default: 3600.0).")
    p_cons.add_argument("--json", action="store_true", help="Output raw JSON summary.")

    # 6. stats
    p_stats = subparsers.add_parser("stats", help="Output memory telemetry and substrate metrics.")
    p_stats.add_argument("-d", "--detailed", action="store_true", help="Include detailed topic and storage breakdown.")
    p_stats.add_argument("--json", action="store_true", help="Output raw JSON.")

    # 7. serve
    p_serve = subparsers.add_parser("serve", help="Launch the Google Material 3 Memory Studio Web UI.")
    p_serve.add_argument("-H", "--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1).")
    p_serve.add_argument("-p", "--port", type=int, default=8765, help="HTTP port (default: 8765).")
    p_serve.add_argument("-b", "--open-browser", action="store_true", help="Automatically open browser.")

    # 8. mcp
    p_mcp = subparsers.add_parser("mcp", help="Run Model Context Protocol (MCP) server over stdio.")

    # 9. diagnostics / platform / doctor
    for diag_alias in ("platform", "doctor", "diagnostics"):
        p_diag = subparsers.add_parser(diag_alias, help="System health check & diagnostics report.")
        p_diag.add_argument("-v", "--verbose", action="store_true", help="Detailed inspection.")
        p_diag.add_argument("--json", action="store_true", help="Output raw JSON.")

    # 10. test
    p_test = subparsers.add_parser("test", help="Run internal self-verification test runner.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    _init_colors(no_color=args.no_color)

    if not args.command:
        print_banner()
        parser.print_help()
        return 0

    dispatch = {
        "store": handle_store,
        "recall": handle_recall,
        "search": handle_search,
        "graph": handle_graph,
        "consolidate": handle_consolidate,
        "stats": handle_stats,
        "serve": handle_serve,
        "mcp": handle_mcp,
        "platform": handle_diagnostics,
        "doctor": handle_diagnostics,
        "diagnostics": handle_diagnostics,
        "test": handle_test,
    }

    handler = dispatch.get(args.command)
    if handler:
        return handler(args)
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
