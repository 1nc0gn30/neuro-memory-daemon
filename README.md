# Neuro-Memory Daemon (`neuro-memory-daemon`)

Zero-dependency Python cognitive memory substrate, 3-factor Spike-Timing-Dependent Plasticity (STDP) engine, 28-route HTTP workstation (`127.0.0.1:8094`), Obsidian Second Brain vault synchronizer, and 21-tool Model Context Protocol (MCP) server.

[![CI](https://github.com/NullAITech/neuro-memory-daemon/actions/workflows/ci.yml/badge.svg)](https://github.com/NullAITech/neuro-memory-daemon/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## Cognitive Substrate Architecture

`neuro-memory-daemon` implements persistent associative agent memory using standard-library Python (`sqlite3` WAL, `math`, `http.server`, `threading`) with zero third-party runtime dependencies:

1. **3-Factor Spike-Timing-Dependent Plasticity (STDP)**:
   - Updates synaptic edge weights between co-activated memory engrams according to $\Delta w = \eta \cdot \text{DA} \cdot \exp(-|\Delta t|/\tau)$, supporting reward-modulated Long-Term Potentiation (LTP) and Long-Term Depression (LTD).
2. **Hippocampal CA3/CA1 Auto-Associative Recall & Pattern Separation**:
   - Spreading activation across weighted adjacency edges reconstructs full memory engrams from partial query cues while orthogonalizing overlapping traces.
3. **DLPFC Working Memory & Ebbinghaus Retention Decay**:
   - Bounded LRU working buffer ($7 \pm 2$ active slots) paired with exponential retention decay $R(t) = \exp(-\Delta t / S)$ and sharp-wave ripple (SWR) consolidation passes that prune sub-threshold noise.
4. **Endogenous Neuromodulation & Yerkes-Dodson Arousal**:
   - Tracks Norepinephrine (`NE`, flashbulb memory lock at $\text{NE} \ge 0.85$), Dopamine (`DA`, plasticity gain), Acetylcholine (`ACh`, sensory encoding vs. internal consolidation), and Serotonin (`5-HT`).
5. **Bidirectional Obsidian Second Brain Integration**:
   - Indexes and audits Obsidian Flavored Markdown (`[[Wikilinks]]`, frontmatter, callouts), JSON Canvas 1.0 (`.canvas`), Obsidian Bases (`.base`), and LLM Wiki synthesis pages with fixed-root path confinement.
6. **3D WebGL Cortex & Memory Studio UI (`127.0.0.1:8094`)**:
   - Interactive Three.js visualization of six semantic clusters (`Agents`, `Tools`, `Security`, `System`, `Living Minds`, `Obsidian Second Brain`), multi-hop Dijkstra pathway tracing, salience threshold scrubbing, and dual-pane note editing.

---

## Installation & Quick Start

```bash
git clone https://github.com/NullAITech/neuro-memory-daemon.git
cd neuro-memory-daemon
pip install -e .

# Launch the HTTP daemon & WebGL Memory Studio on http://127.0.0.1:8094
neuro-memory serve --port 8094
curl -s http://127.0.0.1:8094/health
```

---

## CLI Reference (`neuro-memory` / `neuro-memory-daemon`)

```bash
# Encode an associative memory engram
neuro-memory store "Configured SQLite WAL journaling for concurrent readers" \
  --tags "sqlite,wal,storage" --category "architecture" --importance 1.2

# CA3 pattern-completion recall & filtered search
neuro-memory recall "sqlite concurrency" --top-k 5
neuro-memory search "WAL" --tag "storage"

# Export synaptic adjacency topology
neuro-memory graph --format json
neuro-memory graph --format mermaid

# Trigger sleep consolidation, neuromodulation, flashbulb lock, and diagnostics
neuro-memory consolidate --decay-rate 0.05 --prune-threshold 0.05
neuro-memory neuromodulate --pulse --ne 0.25 --da 0.30
neuro-memory flashbulb <memory-id> --salience 1.5 --reason "Verified failover path"
neuro-memory stats --detailed
neuro-memory doctor
```

---

## 21-Tool Model Context Protocol (MCP) Server

Supports both stdio (`neuro-memory mcp` / `python3 -m neuro_memory_daemon.mcp_server`) and HTTP JSON-RPC 2.0 (`POST /api/mcp` on `127.0.0.1:8094`).

### Cognitive Substrate Tools (11)
- `memory_store`, `memory_recall`, `memory_search`, `memory_graph`, `memory_consolidate`, `memory_stats`, `memory_diagnostics`, `memory_metacognition`, `neuro_neuromodulator_status`, `neuro_neuromodulate_pulse`, `neuro_flashbulb_tag`

### Obsidian Second Brain & Layer-1 Tools (10)
- `obsidian_vault_search`, `obsidian_wiki_synthesize`, `obsidian_canvas_generate`, `obsidian_doctor_audit`, `obsidian_daily_log`, `obsidian_backlinks_inspect`, `obsidian_bundle_export`, `obsidian_note_read`, `obsidian_note_write`, `obsidian_vaelor_pouw`

### Client Registration (`claude_desktop_config.json` / `.cursor/mcp.json`)

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

## Python Library API

```python
from neuro_memory_daemon import consolidate_memories, recall_memory, store_memory

store_memory(
    text="Implemented loopback Origin verification on local daemons",
    tags=["security", "cors", "http"],
    category="security",
    importance=1.3,
)
matches = recall_memory("loopback origin", top_k=3)
consolidate_memories(decay_rate=0.05)
```

---

## Verification & Test Suite

```bash
PYTHONPATH=src python3 -m pytest tests/ -v   # 165 unit & integration tests
gitleaks detect --source . --no-banner --redact
```

---

## License & Support

- **License**: Apache-2.0
- **Open Access**: 100% free and open-source with zero paywalls or locked tools.
- **Support**: [Buy Us a Coffee via Stripe](https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X)

Engineered by **1nc0gn30** ([@1nc0gn30](https://github.com/1nc0gn30) · [1nc0gn30.si](https://1nc0gn30.si)) · [NullAI Platform](https://nullai.tech) · [Zoth Studio](https://zoth.nullai.tech)
