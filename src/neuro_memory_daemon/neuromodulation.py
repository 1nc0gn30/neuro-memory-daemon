"""Neuromodulation Engine: Locus Coeruleus, Yerkes-Dodson Curve & Flashbulb Consolidation.

Implements neuroscience-grounded neuromodulation algorithms:
1. 4-Factor Neuromodulatory Vector:
   - Norepinephrine (NE, [0.0, 1.0]): Arousal, vigilance, and flashbulb memory gating.
     High NE (>= 0.85) triggers permanent Long-Term Potentiation (LTP) tagging
     and Ebbinghaus decay immunity.
   - Dopamine (DA, [-1.0, 1.0]): Reward Prediction Error (RPE) gating 3-factor STDP
     synaptic plasticity (positive RPE reinforces LTP, negative induces LTD).
   - Acetylcholine (ACh, [0.0, 1.0]): Sensory encoding vs internal consolidation switch.
     High ACh (> 0.6) = external sensory encoding; Low ACh (< 0.4) = internal sleep/replay.
   - Serotonin (5-HT, [0.0, 1.0]): Behavioral patience and temporal discounting horizon.
2. Yerkes-Dodson Law of Arousal:
   - Evaluates cognitive task efficiency as an inverted-U function of arousal and task complexity.
   - Differentiates simple (high optimal arousal) from complex (low optimal arousal) tasks.
3. Three-Factor Spike-Timing-Dependent Plasticity (STDP):
   - Modulates Hebbian eligibility traces by dopaminergic reward prediction error.
4. Flashbulb Memory Consolidation Engine:
   - Tags high-salience traumatic or critical cognitive events into immutable,
     zero-decay permanent engrams.

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from neuro_memory_daemon.storage import MemoryRecord, StorageEngine, normalize_tags


class CognitiveMode(str, Enum):
    """Modes of hippocampal-cortical processing modulated by Acetylcholine (ACh)."""
    ENCODING = "ENCODING"                      # High ACh (> 0.6): external sensory ingestion
    CONSOLIDATION_REPLAY = "CONSOLIDATION"    # Low ACh (< 0.4): internal replay & schema consolidation
    BALANCED = "BALANCED"                      # Intermediate ACh (0.4 - 0.6): dual processing


class ArousalZone(str, Enum):
    """Cognitive efficiency state on the Yerkes-Dodson curve."""
    UNDER_AROUSED = "UNDER_AROUSED"  # Hypo-vigilant / sluggish / low activation
    OPTIMAL_FLOW = "OPTIMAL_FLOW"    # Peak performance inverted-U zenith
    OVER_AROUSED = "OVER_AROUSED"    # Hyper-vigilant / cognitive narrowing / panic


@dataclass
class NeuromodulatorLevels:
    """Current concentration of neurotransmitters and neuromodulators."""

    norepinephrine: float = 0.5   # Arousal, vigilance (0.0 to 1.0)
    dopamine: float = 0.0         # Reward Prediction Error (-1.0 to 1.0)
    acetylcholine: float = 0.5    # Encoding vs consolidation (0.0 to 1.0)
    serotonin: float = 0.5        # Cognitive patience / delay discounting (0.0 to 1.0)

    def __post_init__(self) -> None:
        self.norepinephrine = max(0.0, min(1.0, float(self.norepinephrine)))
        self.dopamine = max(-1.0, min(1.0, float(self.dopamine)))
        self.acetylcholine = max(0.0, min(1.0, float(self.acetylcholine)))
        self.serotonin = max(0.0, min(1.0, float(self.serotonin)))

    def to_dict(self) -> Dict[str, float]:
        return {
            "norepinephrine": round(self.norepinephrine, 4),
            "dopamine": round(self.dopamine, 4),
            "acetylcholine": round(self.acetylcholine, 4),
            "serotonin": round(self.serotonin, 4),
        }


@dataclass
class YerkesDodsonResult:
    """Evaluation result for cognitive efficiency under Yerkes-Dodson Law."""

    arousal: float
    task_complexity: float
    optimal_arousal: float
    efficiency: float
    zone: ArousalZone
    tolerance_window: float
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arousal": round(self.arousal, 4),
            "task_complexity": round(self.task_complexity, 4),
            "optimal_arousal": round(self.optimal_arousal, 4),
            "efficiency": round(self.efficiency, 4),
            "zone": self.zone.value,
            "tolerance_window": round(self.tolerance_window, 4),
            "recommendation": self.recommendation,
        }


@dataclass
class ThreeFactorSTDPResult:
    """Outcome of 3-factor Dopamine-gated synaptic update."""

    source: str
    target: str
    delta_t: float
    dopamine_rpe: float
    delta_weight: float
    previous_weight: float
    new_weight: float
    plasticity_type: str  # "LTP_POTENTIATED", "LTD_DEPRESSED", "NEUTRAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "delta_t": round(self.delta_t, 4),
            "dopamine_rpe": round(self.dopamine_rpe, 4),
            "delta_weight": round(self.delta_weight, 4),
            "previous_weight": round(self.previous_weight, 4),
            "new_weight": round(self.new_weight, 4),
            "plasticity_type": self.plasticity_type,
        }


@dataclass
class FlashbulbTagResult:
    """Result of marking a memory trace as a permanent flashbulb engram."""

    memory_id: str
    salience: float
    previous_decay: float
    new_decay: float
    immutable: bool
    tags_added: List[str]
    reason: str
    timestamp: float
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["timestamp"] = round(self.timestamp, 3)
        return res


# ---------------------------------------------------------------------------
# Algorithmic Functions
# ---------------------------------------------------------------------------

def calculate_yerkes_dodson_efficiency(
    arousal: float,
    task_complexity: float = 0.5,
) -> YerkesDodsonResult:
    """Calculate cognitive efficiency according to the Yerkes-Dodson inverted-U law.

    Mathematical formulation:
    - Simple tasks (complexity -> 0.0): optimal arousal is high (~0.85), broad tolerance (~0.35).
    - Complex tasks (complexity -> 1.0): optimal arousal is low (~0.30), narrow tolerance (~0.20).
    - Optimal arousal: A*(c) = 0.85 - 0.55 * c
    - Tolerance: sigma(c) = 0.35 - 0.15 * c
    - Efficiency: exp( - (A - A*)^2 / (2 * sigma^2) )

    Args:
        arousal: Current arousal level in [0.0, 1.0] (driven by Norepinephrine).
        task_complexity: Complexity of task in [0.0, 1.0] (0 = simple/motor, 1 = deep reasoning).

    Returns:
        YerkesDodsonResult with calculated efficiency score and cognitive zone.
    """
    a = max(0.0, min(1.0, float(arousal)))
    c = max(0.0, min(1.0, float(task_complexity)))

    optimal_a = 0.85 - (0.55 * c)
    sigma = 0.35 - (0.15 * c)

    diff = a - optimal_a
    efficiency = math.exp(- (diff ** 2) / (2.0 * (sigma ** 2)))
    efficiency = round(max(0.01, min(1.0, efficiency)), 4)

    if diff < -sigma:
        zone = ArousalZone.UNDER_AROUSED
        rec = (
            f"Arousal ({a:.2f}) is below optimal ({optimal_a:.2f}) for complexity {c:.2f}. "
            "Suggest increasing cognitive engagement, stimulus pacing, or norepinephrine pulse."
        )
    elif diff > sigma:
        zone = ArousalZone.OVER_AROUSED
        rec = (
            f"Arousal ({a:.2f}) exceeds optimal ({optimal_a:.2f}) for complexity {c:.2f}. "
            "High stress/vigilance may narrow cognitive bandwidth. Suggest relaxation or decreasing task complexity."
        )
    else:
        zone = ArousalZone.OPTIMAL_FLOW
        rec = (
            f"Arousal ({a:.2f}) is in optimal flow zone for complexity {c:.2f}. "
            f"Cognitive efficiency is {efficiency * 100:.1f}%."
        )

    return YerkesDodsonResult(
        arousal=a,
        task_complexity=c,
        optimal_arousal=round(optimal_a, 4),
        efficiency=efficiency,
        zone=zone,
        tolerance_window=round(sigma, 4),
        recommendation=rec,
    )


def calculate_three_factor_stdp(
    current_weight: float,
    delta_t: float,
    dopamine_rpe: float,
    eta: float = 0.25,
    tau: float = 60.0,
) -> Tuple[float, float, str]:
    """Calculate 3-factor Dopamine-gated Spike-Timing-Dependent Plasticity.

    Standard STDP Hebbian trace: E = exp(-|delta_t| / tau)
    Modulatory factor: Dopamine Reward Prediction Error (DA in [-1.0, 1.0])
    Delta W = eta * DA * exp(-|delta_t| / tau)

    Args:
        current_weight: Current synaptic connection weight (0.0 to 1.0).
        delta_t: Time difference between pre- and post-synaptic events in seconds.
        dopamine_rpe: Dopamine prediction error in [-1.0, 1.0].
        eta: Plasticity learning rate constant (default: 0.25).
        tau: Plasticity temporal decay window in seconds (default: 60.0).

    Returns:
        Tuple of (delta_weight, new_weight, plasticity_type).
    """
    w = max(0.0, min(1.0, float(current_weight)))
    rpe = max(-1.0, min(1.0, float(dopamine_rpe)))
    dt = abs(delta_t)
    tau = max(1.0, float(tau))

    trace = math.exp(-dt / tau)
    dw = eta * rpe * trace

    if rpe > 0.001:
        # Long-Term Potentiation (LTP) with soft saturation towards 1.0
        new_w = min(1.0, w + dw * (1.0 - w))
        ptype = "LTP_POTENTIATED"
    elif rpe < -0.001:
        # Long-Term Depression (LTD) with floor at 0.01
        new_w = max(0.01, w + dw * w)  # dw is negative
        ptype = "LTD_DEPRESSED"
    else:
        new_w = w
        dw = 0.0
        ptype = "NEUTRAL"

    return round(dw, 4), round(new_w, 4), ptype


def flashbulb_tag_memory(
    storage_or_daemon: Any,
    memory_id: str,
    salience: float = 1.0,
    reason: str = "High-arousal flashbulb emotional tag",
    arousal: float = 0.9,
) -> FlashbulbTagResult:
    """Tag a memory trace as a permanent, non-decaying flashbulb engram.

    Flashbulb memories represent indelible traces formed under acute norepinephrine
    release (Yerkes-Dodson peak arousal). They are permanently immune to Ebbinghaus
    forgetting curves (decay_factor locked to 0.05, immutable flag set to True).

    Args:
        storage_or_daemon: StorageEngine or MemoryDaemon instance.
        memory_id: Target memory identifier.
        salience: Subjective emotional or cognitive salience (0.0 to 1.0+).
        reason: Human-readable rationale for flashbulb locking.
        arousal: Triggering norepinephrine arousal level (>= 0.85).

    Returns:
        FlashbulbTagResult with confirmation and decay changes.
    """
    now = time.time()
    tags_to_add = ["flashbulb", "salient"]

    # Support both StorageEngine and MemoryDaemon instances
    if hasattr(storage_or_daemon, "get_memory") and hasattr(storage_or_daemon, "save_memory"):
        # StorageEngine instance
        mem: Optional[MemoryRecord] = storage_or_daemon.get_memory(memory_id)
        if not mem:
            return FlashbulbTagResult(
                memory_id=memory_id,
                salience=salience,
                previous_decay=1.0,
                new_decay=1.0,
                immutable=False,
                tags_added=[],
                reason=reason,
                timestamp=now,
                success=False,
                error=f"Memory record '{memory_id}' not found in storage.",
            )

        prev_decay = mem.decay_factor
        mem.decay_factor = 0.05
        mem.immutable = True
        mem.importance = max(mem.importance, min(1.0, mem.importance + 0.3))

        existing_tags = set(mem.tags)
        for t in tags_to_add:
            existing_tags.add(t)
        mem.tags = normalize_tags(list(existing_tags))

        if not isinstance(mem.metadata, dict):
            mem.metadata = {}
        mem.metadata["flashbulb"] = {
            "tagged_at": now,
            "salience": float(salience),
            "reason": str(reason),
            "arousal_level": float(arousal),
        }

        storage_or_daemon.save_memory(mem)

        return FlashbulbTagResult(
            memory_id=memory_id,
            salience=salience,
            previous_decay=prev_decay,
            new_decay=0.05,
            immutable=True,
            tags_added=tags_to_add,
            reason=reason,
            timestamp=now,
            success=True,
        )

    elif hasattr(storage_or_daemon, "nodes"):
        # MemoryDaemon instance
        with getattr(storage_or_daemon, "_lock"):
            nodes = storage_or_daemon.nodes
            if memory_id not in nodes:
                return FlashbulbTagResult(
                    memory_id=memory_id,
                    salience=salience,
                    previous_decay=1.0,
                    new_decay=1.0,
                    immutable=False,
                    tags_added=[],
                    reason=reason,
                    timestamp=now,
                    success=False,
                    error=f"Memory node '{memory_id}' not found in daemon substrate.",
                )

            node = nodes[memory_id]
            prev_decay = float(node.metadata.get("decay_factor", 1.0))
            node.metadata["decay_factor"] = 0.05
            node.metadata["immutable"] = True
            node.importance = max(node.importance, min(1.0, node.importance + 0.3))

            existing_tags = set(node.tags)
            for t in tags_to_add:
                existing_tags.add(t)
            node.tags = sorted(existing_tags)

            node.metadata["flashbulb"] = {
                "tagged_at": now,
                "salience": float(salience),
                "reason": str(reason),
                "arousal_level": float(arousal),
            }

            if hasattr(storage_or_daemon, "_save"):
                storage_or_daemon._save()

            return FlashbulbTagResult(
                memory_id=memory_id,
                salience=salience,
                previous_decay=prev_decay,
                new_decay=0.05,
                immutable=True,
                tags_added=tags_to_add,
                reason=reason,
                timestamp=now,
                success=True,
            )

    else:
        return FlashbulbTagResult(
            memory_id=memory_id,
            salience=salience,
            previous_decay=1.0,
            new_decay=1.0,
            immutable=False,
            tags_added=[],
            reason=reason,
            timestamp=now,
            success=False,
            error=f"Invalid storage or daemon object: {type(storage_or_daemon)}",
        )


# ---------------------------------------------------------------------------
# Neuromodulatory System Controller
# ---------------------------------------------------------------------------

class NeuromodulatorySystem:
    """Locus Coeruleus & Basal Forebrain Neuromodulation Controller.

    Manages real-time chemical dynamics for cognitive arousal, reward reinforcement,
    attentional gating, and consolidation switches.
    """

    def __init__(
        self,
        baseline_norepinephrine: float = 0.5,
        baseline_dopamine: float = 0.0,
        baseline_acetylcholine: float = 0.5,
        baseline_serotonin: float = 0.5,
        decay_half_life_seconds: float = 300.0,
    ) -> None:
        """Initialize neuromodulatory system with baseline set-points.

        Args:
            baseline_norepinephrine: Homeostatic baseline for NE (0.0 - 1.0).
            baseline_dopamine: Homeostatic baseline for DA (-1.0 - 1.0).
            baseline_acetylcholine: Homeostatic baseline for ACh (0.0 - 1.0).
            baseline_serotonin: Homeostatic baseline for 5-HT (0.0 - 1.0).
            decay_half_life_seconds: Relaxation rate back toward baseline.
        """
        self.baseline_ne = max(0.0, min(1.0, baseline_norepinephrine))
        self.baseline_da = max(-1.0, min(1.0, baseline_dopamine))
        self.baseline_ach = max(0.0, min(1.0, baseline_acetylcholine))
        self.baseline_5ht = max(0.0, min(1.0, baseline_serotonin))
        self.half_life = max(1.0, decay_half_life_seconds)

        self.current = NeuromodulatorLevels(
            norepinephrine=self.baseline_ne,
            dopamine=self.baseline_da,
            acetylcholine=self.baseline_ach,
            serotonin=self.baseline_5ht,
        )
        self.last_update_time = time.time()
        self.total_pulses_injected = 0
        self.flashbulb_events_count = 0

    def step_decay(self, current_time: Optional[float] = None) -> NeuromodulatorLevels:
        """Apply passive exponential decay toward homeostatic baseline set-points."""
        now = current_time if current_time is not None else time.time()
        dt = max(0.0, now - self.last_update_time)
        self.last_update_time = now

        if dt > 0:
            decay_factor = math.exp(- (dt * math.log(2)) / self.half_life)
            self.current.norepinephrine = self.baseline_ne + (self.current.norepinephrine - self.baseline_ne) * decay_factor
            self.current.dopamine = self.baseline_da + (self.current.dopamine - self.baseline_da) * decay_factor
            self.current.acetylcholine = self.baseline_ach + (self.current.acetylcholine - self.baseline_ach) * decay_factor
            self.current.serotonin = self.baseline_5ht + (self.current.serotonin - self.baseline_5ht) * decay_factor

        return self.current

    def pulse(
        self,
        ne_delta: float = 0.0,
        da_delta: float = 0.0,
        ach_delta: float = 0.0,
        serotonin_delta: float = 0.0,
    ) -> NeuromodulatorLevels:
        """Inject a neurochemical pulse into the system.

        Args:
            ne_delta: Norepinephrine shift (positive = heightened arousal/alarm).
            da_delta: Dopamine RPE shift (positive = reward, negative = punishment).
            ach_delta: Acetylcholine shift (positive = sensory encoding, negative = consolidation).
            serotonin_delta: Serotonin shift (positive = patience/stabilization).

        Returns:
            Updated NeuromodulatorLevels.
        """
        self.step_decay()
        self.current.norepinephrine = max(0.0, min(1.0, self.current.norepinephrine + ne_delta))
        self.current.dopamine = max(-1.0, min(1.0, self.current.dopamine + da_delta))
        self.current.acetylcholine = max(0.0, min(1.0, self.current.acetylcholine + ach_delta))
        self.current.serotonin = max(0.0, min(1.0, self.current.serotonin + serotonin_delta))
        self.total_pulses_injected += 1
        return self.current

    def set_levels(
        self,
        ne: Optional[float] = None,
        da: Optional[float] = None,
        ach: Optional[float] = None,
        serotonin: Optional[float] = None,
    ) -> NeuromodulatorLevels:
        """Explicitly override neuromodulator levels."""
        self.last_update_time = time.time()
        if ne is not None:
            self.current.norepinephrine = max(0.0, min(1.0, float(ne)))
        if da is not None:
            self.current.dopamine = max(-1.0, min(1.0, float(da)))
        if ach is not None:
            self.current.acetylcholine = max(0.0, min(1.0, float(ach)))
        if serotonin is not None:
            self.current.serotonin = max(0.0, min(1.0, float(serotonin)))
        return self.current

    def get_cognitive_mode(self) -> CognitiveMode:
        """Determine whether system is configured for sensory encoding or internal consolidation."""
        self.step_decay()
        ach = self.current.acetylcholine
        if ach > 0.6:
            return CognitiveMode.ENCODING
        elif ach < 0.4:
            return CognitiveMode.CONSOLIDATION_REPLAY
        else:
            return CognitiveMode.BALANCED

    def is_flashbulb_threshold_met(self) -> bool:
        """Check if current norepinephrine arousal warrants automatic flashbulb memory tagging."""
        self.step_decay()
        return self.current.norepinephrine >= 0.85

    def evaluate_yerkes_dodson(self, task_complexity: float = 0.5) -> YerkesDodsonResult:
        """Evaluate current cognitive performance potential under Yerkes-Dodson law."""
        self.step_decay()
        return calculate_yerkes_dodson_efficiency(
            arousal=self.current.norepinephrine,
            task_complexity=task_complexity,
        )

    def apply_three_factor_stdp(
        self,
        source: str,
        target: str,
        current_weight: float,
        delta_t: float,
        rpe_override: Optional[float] = None,
        eta: float = 0.25,
        tau: float = 60.0,
    ) -> ThreeFactorSTDPResult:
        """Apply three-factor dopamine-gated STDP using the system's current dopamine state."""
        self.step_decay()
        rpe = self.current.dopamine if rpe_override is None else max(-1.0, min(1.0, float(rpe_override)))
        dw, new_w, ptype = calculate_three_factor_stdp(
            current_weight=current_weight,
            delta_t=delta_t,
            dopamine_rpe=rpe,
            eta=eta,
            tau=tau,
        )
        return ThreeFactorSTDPResult(
            source=source,
            target=target,
            delta_t=delta_t,
            dopamine_rpe=rpe,
            delta_weight=dw,
            previous_weight=current_weight,
            new_weight=new_w,
            plasticity_type=ptype,
        )

    def tag_flashbulb(
        self,
        storage_or_daemon: Any,
        memory_id: str,
        salience: float = 1.0,
        reason: str = "High-arousal flashbulb tag",
    ) -> FlashbulbTagResult:
        """Mark a memory trace as a permanent flashbulb engram and update telemetry."""
        self.step_decay()
        res = flashbulb_tag_memory(
            storage_or_daemon=storage_or_daemon,
            memory_id=memory_id,
            salience=salience,
            reason=reason,
            arousal=self.current.norepinephrine,
        )
        if res.success:
            self.flashbulb_events_count += 1
        return res

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive telemetry and diagnostic status of neuromodulatory system."""
        self.step_decay()
        yd = self.evaluate_yerkes_dodson(task_complexity=0.5)
        mode = self.get_cognitive_mode()

        return {
            "levels": self.current.to_dict(),
            "baselines": {
                "norepinephrine": round(self.baseline_ne, 4),
                "dopamine": round(self.baseline_da, 4),
                "acetylcholine": round(self.baseline_ach, 4),
                "serotonin": round(self.baseline_5ht, 4),
            },
            "cognitive_mode": mode.value,
            "flashbulb_ready": self.is_flashbulb_threshold_met(),
            "yerkes_dodson": yd.to_dict(),
            "telemetry": {
                "total_pulses_injected": self.total_pulses_injected,
                "flashbulb_events_count": self.flashbulb_events_count,
                "half_life_seconds": self.half_life,
            },
        }


# ---------------------------------------------------------------------------
# Singleton Instance & Global Accessors
# ---------------------------------------------------------------------------

_GLOBAL_NEUROMODULATORY_SYSTEM: Optional[NeuromodulatorySystem] = None


def get_default_neuromodulatory_system() -> NeuromodulatorySystem:
    """Retrieve or initialize the global singleton NeuromodulatorySystem."""
    global _GLOBAL_NEUROMODULATORY_SYSTEM
    if _GLOBAL_NEUROMODULATORY_SYSTEM is None:
        _GLOBAL_NEUROMODULATORY_SYSTEM = NeuromodulatorySystem()
    return _GLOBAL_NEUROMODULATORY_SYSTEM
