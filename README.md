# 🧠 Neuro-Memory Daemon (`neuro-memory-daemon`)

[![CI](https://github.com/1nc0gn30/neuro-memory-daemon/actions/workflows/ci.yml/badge.svg)](https://github.com/1nc0gn30/neuro-memory-daemon/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0%20external-brightgreen.svg)](pyproject.toml)
[![MCP Native](https://img.shields.io/badge/MCP-2024--11--05-orange.svg)](https://modelcontextprotocol.io/)

> **Cognitive neuroscience-inspired persistent memory daemon and MCP server for autonomous AI agents, swarms, and IDEs.**  
> Features **Spike-Timing-Dependent Plasticity (STDP)**, **Hippocampal CA3/CA1 Pattern Completion**, **Ebbinghaus Forgetting Curves**, and an interactive **Memory Studio (design influenced by Material 3)**. Zero third-party runtime dependencies (100% Python standard library).

---

## 📑 Table of Contents
1. [Core Features](#-core-features)
2. [Cognitive Neuroscience Architecture](#-cognitive-neuroscience-architecture)
   - [Spike-Timing-Dependent Plasticity (STDP)](#1-spike-timing-dependent-plasticity-stdp)
   - [Hippocampal Pattern Completion & Separation (CA3 / CA1)](#2-hippocampal-pattern-completion--separation-ca3--ca1)
   - [DLPFC Working Memory Buffer](#3-dlpfc-working-memory-buffer)
   - [Ebbinghaus Forgetting Curve & Systems Consolidation](#4-ebbinghaus-forgetting-curve--systems-consolidation)
3. [Architecture Diagram](#-architecture-diagram)
4. [Quick Start & Installation](#-quick-start--installation)
5. [CLI Reference Manual](#-cli-reference-manual)
6. [Memory Studio Web UI](#-memory-studio-web-ui)
7. [Model Context Protocol (MCP) Setup](#-model-context-protocol-mcp-setup)
   - [Claude Desktop](#claude-desktop)
   - [Cursor IDE](#cursor-ide)
   - [Cline / VS Code](#cline--vs-code)
   - [OpenClaw & Custom Swarms](#openclaw--custom-swarms)
8. [REST API Reference](#-rest-api-reference)
9. [Python Developer API](#-python-developer-api)
10. [Test Suite & Verification](#-test-suite--verification)

---

## 🌟 Core Features

- ⚡ **Spike-Timing-Dependent Plasticity (STDP)**: Dynamic Hebbian synaptic weight adjustment between entities based on co-occurrence and access timing.
- 🧩 **Hippocampal CA3/CA1 Auto-Associative Recall**: Reconstructs complete memory engrams from partial, degraded query cues while preventing catastrophic interference via pattern separation.
- 🧠 **DLPFC Working Memory Buffer**: High-speed bounded LRU buffer (Miller's Law capacity) for active conversational scratchpad tracking.
- 📉 **Ebbinghaus Decay & Cognitive Sleep Consolidation**: Exponential forgetting dynamics that consolidate high-repetition short-term memories into stable long-term semantic knowledge while pruning ephemeral noise.
- 🎨 **Memory Studio Web UI**: Standalone interactive Light/Dark mode dashboard (design influenced by Material 3) with live Canvas Force-Directed graph, stream feed, recall playground, and telemetry.
- 🔌 **Native Model Context Protocol (MCP)**: Full JSON-RPC 2.0 stdio server ready for immediate plug-and-play with Claude Desktop, Cursor, Cline, and Hermes Agent.
- 🛡️ **Zero External Runtime Dependencies**: 100% Python standard library (sqlite3, json, math, re, http.server, threading, dataclasses).

---

## 🔬 Cognitive Neuroscience Architecture

`neuro-memory-daemon` models biological memory processes rather than treating memory as a naive vector database:

```
                  ┌────────────────────────────────────────┐
                  │          PERCEPTUAL INPUT / CUE         │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │   DLPFC Working Memory Buffer (LRU)    │
                  └───────────────────┬────────────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
  ┌──────────────────────────┐                  ┌──────────────────────────┐
  │  CA3 Pattern Completion  │                  │  Dentate Gyrus / CA1     │
  │  (Auto-Associative Net)  │                  │  Pattern Separation      │
  └────────────┬─────────────┘                  └────────────┬─────────────┘
               │                                             │
               └──────────────────────┬──────────────────────┘
                                      ▼
                  ┌────────────────────────────────────────┐
                  │    STDP Synaptic Plasticity Engine     │
                  │   (Long-Term Potentiation/Depression)  │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │   Systems Consolidation & Sleep Pass   │
                  │   (Ebbinghaus Forgetting: R = e^-t/S)  │
                  └────────────────────────────────────────┘
```

### 1. Spike-Timing-Dependent Plasticity (STDP)
Synapses between concepts are reinforced whenever they are co-activated:
$$\Delta w = A_+ \cdot e^{-\frac{|\Delta t|}{\tau_+}}$$
$$w_{\text{new}} = \min(1.0, w_{\text{old}} + \Delta w \cdot (1 - w_{\text{old}}))$$

### 2. Hippocampal Pattern Completion & Separation (CA3 / CA1)
- **CA3 (Cornu Ammonis 3)**: Spreading activation across recurrent collateral synaptic links reconstructs missing attributes when provided fragmented query cues.
- **Dentate Gyrus / CA1**: Calculates orthogonal residual tokens to assign disambiguating tags and prevent catastrophic overlap.

### 3. DLPFC Working Memory Buffer
Maintains an active Miller's Law buffer ($7 \pm 2$ items) for low-latency retrieval of in-flight session context, providing priming boosts to recently accessed items.

### 4. Ebbinghaus Forgetting Curve & Systems Consolidation
Memory traces passively decay over time according to Hermann Ebbinghaus's exponential forgetting law:
$$R(t) = \exp\left(-\frac{\Delta t}{S}\right)$$
where Stability $S = S_0 \cdot \text{decay\_factor} \cdot (1 + \ln(1 + \text{access\_count})) \cdot (1 + \text{importance})$.

During sleep consolidation passes, memories with $\ge 5$ accesses are promoted to semantic insights with elevated decay resistance, while sub-threshold dead traces are pruned.

### 5. Locus Coeruleus Neuromodulation & Yerkes-Dodson Arousal Curve
Models biological neurotransmitter dynamics to modulate cognitive execution:
- **Norepinephrine (NE, $[0.0, 1.0]$)**: Arousal and vigilance. At high arousal ($\text{NE} \ge 0.85$), emotional/cognitive salience triggers **Flashbulb Consolidation**, locking $\text{decay\_factor} = 0.05$ and $\text{immutable} = \text{True}$.
- **Dopamine (DA, $[-1.0, 1.0]$)**: Reward Prediction Error (RPE) gating 3-factor STDP:
  $$\Delta W = \eta \cdot \text{DA} \cdot \exp\left(-\frac{|\Delta t|}{\tau}\right)$$
  Positive RPE induces Long-Term Potentiation (LTP); negative RPE triggers Long-Term Depression (LTD).
- **Acetylcholine (ACh, $[0.0, 1.0]$)**: Sensory encoding vs. internal consolidation switch:
  - High $\text{ACh} > 0.6 \implies$ `ENCODING` (sensory intake).
  - Low $\text{ACh} < 0.4 \implies$ `CONSOLIDATION` (hippocampal sharp-wave ripples / memory replay).
- **Serotonin (5-HT, $[0.0, 1.0]$)**: Cognitive patience and temporal discounting horizon.
- **Yerkes-Dodson Inverted-U Law**: Computes cognitive efficiency $\eta(A, c) = \exp\left(-\frac{(A - A^*(c))^2}{2 \sigma(c)^2}\right)$ given arousal $A$ and task complexity $c$. Optimal arousal is high ($~0.80$) for simple tasks and lower ($~0.35$) for complex reasoning tasks.

---

## 🚀 Quick Start & Installation

### Standard Installation
```bash
# Clone repository
git clone https://github.com/1nc0gn30/neuro-memory-daemon.git
cd neuro-memory-daemon

# Install in editable mode
pip install -e .
```

### Run Memory Studio Web UI
```bash
neuro-memory serve --port 8788 --open-browser
```
Visit `http://localhost:8788` to explore the Memory Studio (design influenced by Material 3)!

---

## 💻 CLI Reference Manual

The `neuro-memory` (or `neuro-memory-daemon`) CLI provides rich subcommands:

```bash
# Store memory engram
neuro-memory store "Refactored SQLite schema with WAL journaling" \
  --tags "sqlite, database, wal, performance" \
  --category "architecture" \
  --importance 1.2

# Associative Pattern Completion Recall
neuro-memory recall "sqlite performance" --top-k 5

# Full-text & Tag Filtered Search
neuro-memory search "WAL" --tag "database"

# Export Synaptic Topology Graph
neuro-memory graph --format mermaid
neuro-memory graph --format json
neuro-memory graph --format ascii

# Trigger Cognitive Sleep Consolidation
neuro-memory consolidate --decay-rate 0.05 --prune-threshold 0.05

# Telemetry & Diagnostics
neuro-memory stats --detailed
neuro-memory doctor

# Neuromodulation & Yerkes-Dodson Arousal
neuro-memory neuromodulate --complexity 0.7
neuro-memory neuromodulate --pulse --ne 0.25 --da 0.30

# Flashbulb Permanent Engram Tagging
neuro-memory flashbulb <memory-id> --salience 1.5 --reason "Critical failover recovery"
```

---

## 🎨 Memory Studio Web UI

The Memory Studio Web UI delivers a clean light/dark aesthetic (design influenced by Google Material tokens):
- **Interactive Force-Directed Canvas**: Visualize memory nodes, tag clusters, and weighted synaptic links in real time.
- **Engram Feed Stream**: Filter by Category, Agent, or Tags, with Shannon entropy information density indicators.
- **CA3/CA1 Recall Playground**: Test query cues and view real-time pattern completion confidence scores.
- **Neuromodulation & Flashbulb Lab**: Real-time gauges for Norepinephrine, Dopamine, Acetylcholine, Serotonin, 1-click neurochemical pulse injection, interactive Yerkes-Dodson curve simulator, 3-factor STDP playground, and flashbulb consolidation lock.
- **Consolidation Telemetry**: Visual before/after diff of pruned and reinforced synaptic pathways.
- **Quick Ingest Drawer**: Rapid memory encoding with tag auto-suggestions.

---

## 🔌 Model Context Protocol (MCP) Setup

`neuro-memory-daemon` runs natively as an MCP stdio server conforming to protocol version `2024-11-05`.

### Registered MCP Tools:
1. `memory_store`: Store episodic or semantic memory with tags, importance, category, and metadata.
2. `memory_recall`: Perform associative pattern completion recall on query cues.
3. `memory_search`: Full-text and tag-filtered memory search with relevance ranking.
4. `memory_graph`: Export synaptic association graph (JSON, Mermaid, ASCII).
5. `memory_consolidate`: Trigger sleep cycle consolidation (STDP reinforcement & decay pruning).
6. `memory_stats`: Telemetry and substrate statistics.
7. `memory_diagnostics`: System health and diagnostics.
8. `memory_metacognition`: Feeling-of-Knowing (FOK), Tip-of-the-Tongue (TOT), and ACC conflict audit.
9. `neuro_neuromodulator_status`: Query Norepinephrine, Dopamine, Acetylcholine, Serotonin concentrations, and Yerkes-Dodson efficiency.
10. `neuro_neuromodulate_pulse`: Inject chemical pulse to shift arousal, reward error, or encoding mode.
11. `neuro_flashbulb_tag`: Lock high-salience memory trace into permanent flashbulb engram (decay_factor=0.05, immutable=True).

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):
```json
{
  "mcpServers": {
    "neuro-memory": {
      "command": "neuro-memory-daemon",
      "args": ["mcp"]
    }
  }
}
```

### Cursor IDE
Add to `.cursor/mcp.json` or Global MCP settings:
```json
{
  "mcpServers": {
    "neuro-memory": {
      "command": "python3",
      "args": ["-m", "neuro_memory_daemon.cli", "mcp"]
    }
  }
}
```

### Cline / VS Code
Add to `cline_mcp_settings.json`:
```json
{
  "mcpServers": {
    "neuro-memory": {
      "command": "neuro-memory",
      "args": ["mcp"]
    }
  }
}
```

---

## 🌐 REST API Reference

The UI server exposes clean REST endpoints on port `8788`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server health check |
| `GET` | `/api/memories` | List / filter memory engrams (`q`, `category`, `tag`, `limit`) |
| `POST` | `/api/memories` | Store / ingest memory engram |
| `POST` | `/api/recall` | Associative pattern completion recall |
| `GET` | `/api/search` | Filtered memory search |
| `GET` | `/api/graph` | Synaptic adjacency graph (`format=json\|mermaid\|ascii`) |
| `POST` | `/api/consolidate`| Trigger cognitive sleep consolidation |
| `GET` | `/api/stats` | Cognitive telemetry & substrate statistics |
| `GET` | `/api/neuromodulators` | Neuromodulator concentrations, cognitive mode & Yerkes-Dodson curve |
| `POST` | `/api/neuromodulators/pulse` | Inject neurochemical pulse (`ne_delta`, `da_delta`, `ach_delta`, `serotonin_delta`) |
| `POST` | `/api/neuromodulators/levels` | Explicitly set neurotransmitter levels |
| `POST` | `/api/neuromodulators/flashbulb` | Tag memory as permanent flashbulb engram |
| `POST` | `/api/memories/<id>/trigger` | Rehearse & stimulate synaptic node |
| `DELETE`| `/api/memories/<id>` | Delete memory engram |

---

## 🐍 Python Developer API

```python
from neuro_memory_daemon import (
    MemoryDaemon,
    store_memory,
    recall_memory,
    consolidate_memories,
    get_memory_graph,
)

# Ingest memory
res = store_memory(
    text="Configured distributed raft consensus cluster",
    tags=["consensus", "raft", "distributed"],
    category="architecture",
    importance=1.4,
)

# Recall context before executing tasks
recalled = recall_memory("raft consensus algorithm", top_k=3)
for mem in recalled:
    print(f"[{mem['score']*100:.0f}% Resonance] {mem['text']}")

# Run periodic consolidation
stats = consolidate_memories(decay_rate=0.05)
print(f"Consolidated: {stats['strengthened_synapses']} synapses strengthened.")
```

---

## 🧪 Test Suite & Verification

The test suite provides 100% code coverage across storage engines, STDP algorithms, graph visualizers, MCP protocol handlers, CLI commands, and UI server endpoints.

```bash
# Run full pytest suite
pytest tests/ -v

# Run internal self-verification
neuro-memory test
```

---

## 📜 License
Apache-2.0. Open-source and freely extensible for autonomous AI agent research and development.
