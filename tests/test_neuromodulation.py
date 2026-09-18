"""Tests for Neuromodulation, Yerkes-Dodson curve & Flashbulb Consolidation Engine."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Generator

import pytest

from neuro_memory_daemon import (
    ArousalZone,
    CognitiveMode,
    MemoryDaemon,
    NeuromodulatorLevels,
    NeuromodulatorySystem,
    calculate_three_factor_stdp,
    calculate_yerkes_dodson_efficiency,
    flashbulb_tag_memory,
    get_default_neuromodulatory_system,
)
from neuro_memory_daemon.cli import build_parser, main
from neuro_memory_daemon.mcp_server import MCPServer
from neuro_memory_daemon.storage import MemoryRecord, StorageEngine
from neuro_memory_daemon.ui_server import MemoryUIServer, start_server_in_thread


class TestYerkesDodson:
    """Test mathematical validity of Yerkes-Dodson inverted-U arousal law."""

    def test_yerkes_dodson_simple_task(self):
        """Simple tasks (low complexity) have higher optimal arousal (~0.80)."""
        res_low = calculate_yerkes_dodson_efficiency(arousal=0.2, task_complexity=0.1)
        res_opt = calculate_yerkes_dodson_efficiency(arousal=0.8, task_complexity=0.1)
        res_high = calculate_yerkes_dodson_efficiency(arousal=0.98, task_complexity=0.1)

        assert res_low.zone == ArousalZone.UNDER_AROUSED
        assert res_opt.zone == ArousalZone.OPTIMAL_FLOW
        assert res_opt.efficiency > res_low.efficiency
        assert res_opt.efficiency >= 0.95
        assert 0.75 <= res_opt.optimal_arousal <= 0.85
        assert "Arousal" in res_opt.recommendation

    def test_yerkes_dodson_complex_task(self):
        """Complex cognitive reasoning tasks have lower optimal arousal (~0.36)."""
        res_calm = calculate_yerkes_dodson_efficiency(arousal=0.35, task_complexity=0.9)
        res_stressed = calculate_yerkes_dodson_efficiency(arousal=0.9, task_complexity=0.9)

        assert res_calm.zone == ArousalZone.OPTIMAL_FLOW
        assert res_stressed.zone == ArousalZone.OVER_AROUSED
        assert res_calm.efficiency > res_stressed.efficiency
        assert 0.30 <= res_calm.optimal_arousal <= 0.40

    def test_yerkes_dodson_bounds_clamping(self):
        """Values outside [0.0, 1.0] are safely clamped."""
        res_neg = calculate_yerkes_dodson_efficiency(arousal=-0.5, task_complexity=-0.2)
        res_pos = calculate_yerkes_dodson_efficiency(arousal=1.8, task_complexity=1.5)

        assert res_neg.arousal == 0.0
        assert res_neg.task_complexity == 0.0
        assert res_pos.arousal == 1.0
        assert res_pos.task_complexity == 1.0


class TestThreeFactorSTDP:
    """Test 3-factor Dopamine-gated Spike-Timing-Dependent Plasticity."""

    def test_positive_rpe_potentiation(self):
        """Positive Dopamine RPE triggers Long-Term Potentiation (LTP)."""
        dw, new_w, ptype = calculate_three_factor_stdp(
            current_weight=0.3,
            delta_t=10.0,
            dopamine_rpe=0.8,
            eta=0.25,
            tau=60.0,
        )
        assert ptype == "LTP_POTENTIATED"
        assert dw > 0.0
        assert new_w > 0.3

    def test_negative_rpe_depression(self):
        """Negative Dopamine RPE triggers Long-Term Depression (LTD)."""
        dw, new_w, ptype = calculate_three_factor_stdp(
            current_weight=0.7,
            delta_t=10.0,
            dopamine_rpe=-0.7,
            eta=0.25,
            tau=60.0,
        )
        assert ptype == "LTD_DEPRESSED"
        assert dw < 0.0
        assert new_w < 0.7
        assert new_w >= 0.01  # safe floor

    def test_neutral_rpe_preserves_weight(self):
        """Zero Dopamine RPE produces no synaptic weight change."""
        dw, new_w, ptype = calculate_three_factor_stdp(
            current_weight=0.5,
            delta_t=5.0,
            dopamine_rpe=0.0,
        )
        assert ptype == "NEUTRAL"
        assert dw == 0.0
        assert new_w == 0.5

    def test_temporal_decay(self):
        """Spikes further apart in time have smaller plasticity magnitude."""
        dw_near, _, _ = calculate_three_factor_stdp(0.5, delta_t=2.0, dopamine_rpe=1.0)
        dw_far, _, _ = calculate_three_factor_stdp(0.5, delta_t=120.0, dopamine_rpe=1.0)
        assert abs(dw_near) > abs(dw_far)


class TestFlashbulbMemory:
    """Test indelible flashbulb engram tagging and Ebbinghaus decay immunity."""

    def test_flashbulb_tagging_storage_engine(self, storage_in_memory: StorageEngine):
        """StorageEngine records get locked decay_factor=0.05 and immutable=True."""
        record = MemoryRecord(
            id="test-flashbulb-1",
            text="Fatal cluster network partition recovered via Paxos consensus quorum.",
            tags=["paxos", "outage"],
            decay_factor=1.2,
            immutable=False,
        )
        storage_in_memory.save_memory(record)

        res = flashbulb_tag_memory(
            storage_or_daemon=storage_in_memory,
            memory_id="test-flashbulb-1",
            salience=1.5,
            reason="Mission critical infrastructure recovery",
            arousal=0.92,
        )

        assert res.success is True
        assert res.new_decay == 0.05
        assert res.immutable is True
        assert "flashbulb" in res.tags_added

        # Verify persisted state in SQLite
        updated = storage_in_memory.get_memory("test-flashbulb-1")
        assert updated is not None
        assert updated.decay_factor == 0.05
        assert updated.immutable is True
        assert "flashbulb" in updated.tags
        assert "salient" in updated.tags
        assert updated.metadata["flashbulb"]["salience"] == 1.5

    def test_flashbulb_tagging_memory_daemon(self, memory_daemon: MemoryDaemon):
        """MemoryDaemon substrate nodes get tagged as flashbulb."""
        stored = memory_daemon.store(
            "Kernel panic resolved by roll-back of eBPF filter rule.",
            tags=["ebpf", "kernel"],
        )
        mem_id = stored["id"]

        res = memory_daemon.tag_flashbulb(mem_id, salience=1.2, reason="Kernel level fix")
        assert res["success"] is True
        assert res["new_decay"] == 0.05
        assert res["immutable"] is True

        node = memory_daemon.nodes[mem_id]
        assert "flashbulb" in node.tags
        assert node.metadata["decay_factor"] == 0.05
        assert node.metadata["immutable"] is True

    def test_flashbulb_nonexistent_memory(self, storage_in_memory: StorageEngine):
        """Attempting to tag nonexistent memory returns failure result safely."""
        res = flashbulb_tag_memory(storage_in_memory, "nonexistent-id-12345")
        assert res.success is False
        assert "not found" in (res.error or "").lower()


class TestNeuromodulatorySystem:
    """Test NeuromodulatorySystem controller dynamics and homeostatic decay."""

    def test_system_initialization_and_baselines(self):
        ns = NeuromodulatorySystem(
            baseline_norepinephrine=0.5,
            baseline_dopamine=0.0,
            baseline_acetylcholine=0.5,
            baseline_serotonin=0.5,
            decay_half_life_seconds=60.0,
        )
        status = ns.get_status()
        assert status["levels"]["norepinephrine"] == 0.5
        assert status["levels"]["dopamine"] == 0.0
        assert status["cognitive_mode"] == "BALANCED"
        assert status["flashbulb_ready"] is False

    def test_system_pulse_injection(self):
        ns = NeuromodulatorySystem()
        ns.pulse(ne_delta=0.4, da_delta=0.5, ach_delta=0.2, serotonin_delta=-0.1)
        assert ns.current.norepinephrine >= 0.85
        assert ns.is_flashbulb_threshold_met() is True
        assert abs(ns.current.dopamine - 0.5) < 1e-4
        assert ns.get_cognitive_mode() == CognitiveMode.ENCODING
        assert ns.total_pulses_injected == 1

    def test_system_decay_toward_baseline(self):
        ns = NeuromodulatorySystem(decay_half_life_seconds=10.0)
        ns.set_levels(ne=1.0)
        # Advance clock by one half-life (10s)
        now = ns.last_update_time + 10.0
        ns.step_decay(current_time=now)
        # Halfway between 1.0 and baseline 0.5 is 0.75
        assert abs(ns.current.norepinephrine - 0.75) < 0.05

    def test_cognitive_modes(self):
        ns = NeuromodulatorySystem()
        ns.set_levels(ach=0.8)
        assert ns.get_cognitive_mode() == CognitiveMode.ENCODING

        ns.set_levels(ach=0.2)
        assert ns.get_cognitive_mode() == CognitiveMode.CONSOLIDATION_REPLAY

        ns.set_levels(ach=0.5)
        assert ns.get_cognitive_mode() == CognitiveMode.BALANCED


class TestNeuromodulationMCP:
    """Test MCP server tools for neuromodulation."""

    def test_mcp_neuromodulator_tools_list(self, mcp_server: MCPServer):
        req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        resp = mcp_server.handle_request(req)
        assert resp is not None
        names = [t["name"] for t in resp["result"]["tools"]]
        assert "neuro_neuromodulator_status" in names
        assert "neuro_neuromodulate_pulse" in names
        assert "neuro_flashbulb_tag" in names

    def test_mcp_neuromodulator_lifecycle(self, mcp_server: MCPServer):
        # 1. Status query
        status_req = {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "tools/call",
            "params": {"name": "neuro_neuromodulator_status", "arguments": {"task_complexity": 0.7}},
        }
        res = mcp_server.handle_request(status_req)
        assert res is not None and not res["result"].get("isError", False)
        data = json.loads(res["result"]["content"][0]["text"])
        assert "levels" in data
        assert "yerkes_dodson" in data

        # 2. Pulse injection
        pulse_req = {
            "jsonrpc": "2.0",
            "id": 102,
            "method": "tools/call",
            "params": {"name": "neuro_neuromodulate_pulse", "arguments": {"ne_delta": 0.35, "da_delta": 0.2}},
        }
        res_pulse = mcp_server.handle_request(pulse_req)
        assert res_pulse is not None
        pulse_data = json.loads(res_pulse["result"]["content"][0]["text"])
        assert pulse_data["levels"]["norepinephrine"] >= 0.8

        # 3. Store and Flashbulb tag
        store_req = {
            "jsonrpc": "2.0",
            "id": 103,
            "method": "tools/call",
            "params": {
                "name": "memory_store",
                "arguments": {"text": "Zero-day vulnerability patched in auth middleware.", "tags": ["cve", "auth"]},
            },
        }
        store_res = mcp_server.handle_request(store_req)
        mem_id = json.loads(store_res["result"]["content"][0]["text"])["id"]

        tag_req = {
            "jsonrpc": "2.0",
            "id": 104,
            "method": "tools/call",
            "params": {
                "name": "neuro_flashbulb_tag",
                "arguments": {"memory_id": mem_id, "salience": 1.8, "reason": "High severity patch"},
            },
        }
        tag_res = mcp_server.handle_request(tag_req)
        assert tag_res is not None and not tag_res["result"].get("isError", False)
        tag_data = json.loads(tag_res["result"]["content"][0]["text"])
        assert tag_data["success"] is True
        assert tag_data["new_decay"] == 0.05
        assert tag_data["immutable"] is True


class TestNeuromodulationCLI:
    """Test CLI subcommands for neuromodulation."""

    def test_cli_neuromodulate_json(self, capsys):
        code = main(["neuromodulate", "--json"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "levels" in data
        assert "yerkes_dodson" in data

    def test_cli_neuromodulate_pulse(self, capsys):
        code = main(["neuromodulate", "-p", "--ne", "0.2", "--da", "0.3", "--json"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["levels"]["dopamine"] >= 0.25

    def test_cli_flashbulb_tag(self, temp_dir: Path, capsys):
        db_file = str(temp_dir / "cli_flashbulb.json")
        # Store
        code_store = main(["--db-path", db_file, "store", "Database index corrupted and repaired", "--json"])
        assert code_store == 0
        store_out = json.loads(capsys.readouterr().out)
        mem_id = store_out["id"]

        # Tag
        code_tag = main(["--db-path", db_file, "flashbulb", mem_id, "-s", "1.5", "-r", "Corruption recovery", "--json"])
        assert code_tag == 0
        tag_out = json.loads(capsys.readouterr().out)
        assert tag_out["success"] is True
        assert tag_out["new_decay"] == 0.05


class TestNeuromodulationUIServer:
    """Test UI server REST endpoints for neuromodulation."""

    def test_ui_get_neuromodulators(self, live_server):
        _, base_url, _ = live_server
        req = urllib.request.Request(f"{base_url}/api/neuromodulators?complexity=0.8", method="GET")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "levels" in data
            assert data["yerkes_dodson"]["task_complexity"] == 0.8

    def test_ui_post_pulse(self, live_server):
        _, base_url, _ = live_server
        body = json.dumps({"ne_delta": 0.25, "da_delta": 0.35}).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/neuromodulators/pulse",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["levels"]["norepinephrine"] >= 0.6

    def test_ui_post_flashbulb(self, live_server):
        _, base_url, daemon = live_server
        stored = daemon.store("Critical cryptographic key rotated safely", tags=["crypto", "keys"])
        mem_id = stored["id"]

        body = json.dumps({"memory_id": mem_id, "salience": 1.4, "reason": "Key rotation event"}).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/neuromodulators/flashbulb",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["success"] is True
            assert data["new_decay"] == 0.05
            assert data["immutable"] is True
