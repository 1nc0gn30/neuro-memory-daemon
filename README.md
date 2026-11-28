# Neuro-Memory Daemon (`neuro-memory-daemon` v2.9.0)

Zero-dependency Python cognitive memory substrate, 3-factor Spike-Timing-Dependent Plasticity (STDP) engine, hardened loopback HTTP workstation (`127.0.0.1:8094`), Obsidian Second Brain vault synchronizer, and 21-tool Model Context Protocol (MCP) server.

[![CI](https://github.com/1nc0gn30/neuro-memory-daemon/actions/workflows/ci.yml/badge.svg)](https://github.com/1nc0gn30/neuro-memory-daemon/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## What It Does

`neuro-memory-daemon` provides persistent, locally stored associative memory for autonomous AI agents and human operators using standard-library Python (`sqlite3` WAL, `http.server`, `threading`, `math`) with zero pip runtime dependencies and zero external font/CDN egress:

- **Persistent STDP Memory Engrams**: Stores episodic, semantic, procedural, architecture, and security engrams in a local SQLite WAL database (`~/.neuro-memory/`).
- **Associative Recall & Consolidation**: Performs Hippocampal CA3/CA1 pattern completion, spreading activation across weighted synaptic edges, Ebbinghaus retention decay, and sleep consolidation pruning.
- **Dual-Theme 3D WebGL Workstation (`127.0.0.1:8094`)**: Serves Editorial Ivory Light Mode and Obsidian Gold Dark Mode with `?embed=1&theme=light|dark` Zoth Studio integration, 3D Cosmic Neural Nebula, federated Everywhere memory ledger, and Obsidian Second Brain hub.
- **21-Tool MCP Server**: Exposes 11 cognitive substrate tools and 10 Obsidian Second Brain / Vaelor tools over both `stdio` JSON-RPC 2.0 and loopback HTTP `POST /api/mcp`.

---

## How It Works

1. **3-Factor Spike-Timing-Dependent Plasticity (STDP)**:
   - Updates synaptic edge weights between co-activated memory engrams according to $\Delta w = \eta \cdot \text{DA} \cdot \exp(-|\Delta t|/\tau)$, supporting causal Long-Term Potentiation (LTP) and anti-causal Long-Term Depression (LTD).
2. **Hippocampal CA3/CA1 Auto-Associative Recall & Pattern Separation**:
   - Spreading activation across weighted adjacency edges reconstructs full memory engrams from partial query cues while orthogonalizing overlapping traces.
3. **DLPFC Working Memory & Ebbinghaus Retention Decay**:
   - Bounded LRU working buffer ($7 \pm 2$ active slots) paired with exponential retention decay $R(t) = \exp(-\Delta t / S)$ and sharp-wave ripple (SWR) consolidation passes.
4. **Endogenous Neuromodulation & Yerkes-Dodson Arousal**:
   - Tracks Norepinephrine (`NE`, flashbulb memory lock at $\text{NE} \ge 0.85$), Dopamine (`DA`), Acetylcholine (`ACh`), and Serotonin (`5-HT`).
5. **Loopback Security & Fixed-Root Vault Confinement**:
   - Enforces strict loopback `Host` (`127.0.0.1`, `localhost`, `[::1]`) and exact-port `Origin` (`403 Forbidden`) across `GET`, `HEAD`, `POST`, `PUT`, `DELETE`, and `OPTIONS` (reflecting trusted loopback origin only, never wildcard `*`).
   - Emits `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, strict loopback `Content-Security-Policy`, and stripped `Server: Neuro-Memory`.
   - Enforces a `1 MiB` (`413 Payload Too Large`) body cap, strict JSON / numeric query parameter validation (`400 Bad Request` / JSON-RPC `-32700`), DOM-safe rendering, and `Path.resolve().is_relative_to()` confinement on all Obsidian note, wiki, and `.canvas` reads and writes.

---

## Installation & Quick Start

```bash
git clone https://github.com/1nc0gn30/neuro-memory-daemon.git
cd neuro-memory-daemon
pip install -e .

# Launch the HTTP daemon & 3D Memory Studio on http://127.0.0.1:8094
neuro-memory-daemon serve --port 8094
curl -s http://127.0.0.1:8094/health
```

---

## ZothOS CLI & 21-Tool MCP Commands

### CLI Reference (`neuro-memory-daemon`, `neuro-memory`, `zoth-neuro-memory`, `zoth-memory`, `neuro-memory-daemon-tui`)

```bash
# Version, health & live Braille telemetry TUI
neuro-memory-daemon --version
neuro-memory-daemon --json
neuro-memory-daemon-tui --status

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

### 21-Tool Model Context Protocol (MCP) Server

Supports both `stdio` (`neuro-memory mcp` / `python3 -m neuro_memory_daemon.mcp_server`) and loopback HTTP JSON-RPC 2.0 (`POST http://127.0.0.1:8094/api/mcp` and `GET http://127.0.0.1:8094/api/mcp/tools`).

- **Cognitive Substrate Tools (11)**: `memory_store`, `memory_recall`, `memory_search`, `memory_graph`, `memory_consolidate`, `memory_stats`, `memory_diagnostics`, `memory_metacognition`, `neuro_neuromodulator_status`, `neuro_neuromodulate_pulse`, `neuro_flashbulb_tag`
- **Obsidian Second Brain & Vaelor Bridge Tools (10)**: `obsidian_vault_search`, `obsidian_wiki_synthesize`, `obsidian_canvas_generate`, `obsidian_doctor_audit`, `obsidian_daily_log`, `obsidian_backlinks_inspect`, `obsidian_bundle_export`, `obsidian_note_read`, `obsidian_note_write`, `obsidian_vaelor_pouw`

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

## Verification & Test Suite

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest tests/ -q
gitleaks detect --no-git --source .
```

---

## License & Support

- **Version**: `2.9.0`
- **License**: `Apache-2.0`
- **Open Access**: 100% free and open-source with zero paywalls or locked tools.
- **Zoth Studio Route**: [https://zoth.nullai.tech/tools/neuro-memory-daemon](https://zoth.nullai.tech/tools/neuro-memory-daemon)
- **Buy Us a Coffee (Stripe)**: [https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X](https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X)
- **Solana Tip Address**: `GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK` (`solana:GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK`)

Engineered by **Neal Frazier Tech** ([@1nc0gn30](https://github.com/1nc0gn30) · [https://github.com/1nc0gn30/neuro-memory-daemon](https://github.com/1nc0gn30/neuro-memory-daemon)) · [NullAI Platform](https://nullai.tech) · [Zoth Studio](https://zoth.nullai.tech)
