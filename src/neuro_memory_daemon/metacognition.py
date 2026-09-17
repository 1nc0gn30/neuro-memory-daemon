"""Metacognitive Memory Indexing, Epistemic Uncertainty & ACC Conflict Monitor.

Implements cognitive and neuro-architectural metacognition:
1. Feeling-of-Knowing (FOK) & Tip-of-the-Tongue (TOT) State Analyzer:
   - Calculates Epistemic Certainty Score (0.0 to 1.0) based on activation depth,
     associative synaptic density, and retrieval entropy.
   - Categorizes epistemic state: CONFIDENT_RECALL, TIP_OF_THE_TONGUE, or EPISTEMIC_GAP.
   - Proposes bridging associative cues when memory exists in latent synaptic graph
     but surface lexical match is below retrieval threshold.
2. Epistemic Source Attribution & Provenance Rating:
   - Classifies memory origins: PERCEPTUAL, INSTRUCTIONAL, INFERRED, or CONSOLIDATED.
   - Evaluates grounding confidence and flags hallucination / confabulation risk.
3. Anterior Cingulate Cortex (ACC) Cognitive Dissonance & Conflict Detector:
   - Identifies semantic polarity clashes and value discrepancies between active memories.
   - Proposes Hegelian Dialectic resolution (thesis, antithesis, synthesis).

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
import re
import time
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from neuro_memory_daemon.synapse_engine import tokenize, STOP_WORDS


# ---------------------------------------------------------------------------
# Polarity and Contradiction Dictionaries
# ---------------------------------------------------------------------------

POLARITY_PAIRS: List[Tuple[str, str]] = [
    ("enabled", "disabled"),
    ("allow", "deny"),
    ("allowed", "denied"),
    ("permit", "forbid"),
    ("permitted", "forbidden"),
    ("active", "inactive"),
    ("online", "offline"),
    ("connected", "disconnected"),
    ("true", "false"),
    ("success", "failure"),
    ("successful", "failed"),
    ("started", "stopped"),
    ("running", "terminated"),
    ("up", "down"),
    ("valid", "invalid"),
    ("open", "closed"),
    ("secure", "insecure"),
    ("encrypted", "plaintext"),
]

NEGATION_TERMS: Set[str] = {
    "not", "never", "no", "cannot", "can't", "won't", "shouldn't", "mustn't", "neither"
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SourceProvenance:
    """Classifies memory origin and truth grounding."""

    memory_id: str
    provenance_type: str  # PERCEPTUAL, INSTRUCTIONAL, INFERRED, CONSOLIDATED
    grounding_confidence: float  # 0.0 to 1.0
    hallucination_risk: str  # LOW, MODERATE, HIGH
    evidence_signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DialecticConflict:
    """Represents detected cognitive dissonance between two conflicting memory traces."""

    thesis_id: str
    thesis_text: str
    antithesis_id: str
    antithesis_text: str
    conflict_topic: str
    conflict_severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    similarity_context: float
    synthesis_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetacognitiveAuditResult:
    """Complete metacognitive state evaluation for a retrieval cue or memory corpus."""

    query: str
    epistemic_state: str  # CONFIDENT_RECALL, TIP_OF_THE_TONGUE, EPISTEMIC_GAP
    certainty_score: float  # 0.0 to 1.0
    retrieval_entropy: float
    recalled_count: int
    latent_association_score: float
    bridging_cues: List[str] = field(default_factory=list)
    conflicts_detected: List[DialecticConflict] = field(default_factory=list)
    source_attributions: List[SourceProvenance] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["conflicts_detected"] = [c.to_dict() if isinstance(c, DialecticConflict) else c for c in self.conflicts_detected]
        d["source_attributions"] = [s.to_dict() if isinstance(s, SourceProvenance) else s for s in self.source_attributions]
        return d


# ---------------------------------------------------------------------------
# Metacognitive Evaluator Engine
# ---------------------------------------------------------------------------

class MetacognitiveEvaluator:
    """Anterior Cingulate Cortex conflict detection and Feeling-of-Knowing analysis."""

    @staticmethod
    def calculate_distribution_entropy(scores: Sequence[float]) -> float:
        """Compute normalized Shannon entropy of retrieval confidence distribution."""
        if not scores:
            return 0.0
        total = sum(scores)
        if total <= 0.0:
            return 0.0

        probs = [s / total for s in scores if s > 0.0]
        if len(probs) <= 1:
            return 0.0

        raw_entropy = -sum(p * math.log2(p) for p in probs)
        max_entropy = math.log2(len(probs))
        return round(raw_entropy / max_entropy, 4) if max_entropy > 0.0 else 0.0

    @classmethod
    def evaluate_source_provenance(cls, memory_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> SourceProvenance:
        """Categorize epistemic origin of a memory based on linguistic cues and metadata."""
        meta = metadata or {}
        text_lower = text.lower()
        signals: List[str] = []

        # 1. Check metadata hints
        category = str(meta.get("category", "")).lower()
        perspective = str(meta.get("perspective", "")).lower()

        # Instructional patterns
        if any(w in text_lower for w in ["must", "always", "rule", "required", "directive", "forbidden", "never"]):
            prov = "INSTRUCTIONAL"
            signals.append("Directive / rule modal auxiliary verbs detected")
            grounding = 0.95
        # Perceptual / empirical patterns
        elif any(w in text_lower for w in ["http", "error", "traceback", "status 200", "log", "observed", "timestamp", "payload", "output:"]):
            prov = "PERCEPTUAL"
            signals.append("Empirical runtime or network data signatures")
            grounding = 0.92
        # Consolidated patterns
        elif "consolidated" in category or "schema" in category or "replay" in text_lower or meta.get("consolidated"):
            prov = "CONSOLIDATED"
            signals.append("Derived from sleep-replay or recurrent consolidation")
            grounding = 0.88
        # Inferred patterns
        elif any(w in text_lower for w in ["therefore", "suggests", "inferred", "likely", "hypothesize", "assumes", "predicts"]):
            prov = "INFERRED"
            signals.append("Epistemic inference markers detected")
            grounding = 0.75
        else:
            prov = "PERCEPTUAL" if category in ("episodic", "working") else "INFERRED"
            signals.append(f"Inferred default from category '{category}'")
            grounding = 0.80

        # Hallucination risk assessment
        if grounding >= 0.90:
            risk = "LOW"
        elif grounding >= 0.70:
            risk = "MODERATE"
        else:
            risk = "HIGH"

        return SourceProvenance(
            memory_id=memory_id,
            provenance_type=prov,
            grounding_confidence=round(grounding, 3),
            hallucination_risk=risk,
            evidence_signals=signals,
        )

    @classmethod
    def detect_conflicts(
        cls,
        memories: Sequence[Any],  # MemoryNode, MemoryRecord, or dict
    ) -> List[DialecticConflict]:
        """Scan active memory traces for cognitive dissonance, polarity clash, or value contradiction."""
        conflicts: List[DialecticConflict] = []
        parsed: List[Tuple[str, str, Set[str], List[str], Set[str]]] = []

        for m in memories:
            if isinstance(m, dict):
                m_id = str(m.get("id", ""))
                m_text = str(m.get("text", ""))
            elif hasattr(m, "id") and hasattr(m, "text"):
                m_id = str(m.id)
                m_text = str(m.text)
            else:
                continue

            raw_words = set(re.findall(r"\b[a-zA-Z']+\b", m_text.lower()))
            tokens = tokenize(m_text)
            tok_set = set(tokens)
            parsed.append((m_id, m_text, tok_set, tokens, raw_words))

        n = len(parsed)
        for i in range(n):
            id_a, text_a, tokens_a, raw_a, words_a = parsed[i]
            for j in range(i + 1, n):
                id_b, text_b, tokens_b, raw_b, words_b = parsed[j]

                shared_tokens = tokens_a.intersection(tokens_b)
                if len(shared_tokens) < 2:
                    continue  # Unrelated subjects

                jaccard = len(shared_tokens) / len(tokens_a.union(tokens_b))
                topic = " / ".join(list(shared_tokens)[:3])

                # 1. Check for polarity pairs in shared context
                has_polarity_clash = False
                clash_pair: Optional[Tuple[str, str]] = None
                for pos, neg in POLARITY_PAIRS:
                    if (pos in tokens_a and neg in tokens_b) or (neg in tokens_a and pos in tokens_b):
                        has_polarity_clash = True
                        clash_pair = (pos, neg)
                        break

                # 2. Check for negation clash (one has negation, one doesn't)
                has_negation_a = bool(words_a.intersection(NEGATION_TERMS))
                has_negation_b = bool(words_b.intersection(NEGATION_TERMS))
                negation_clash = (has_negation_a != has_negation_b) and (jaccard > 0.40)

                # 3. Check for numerical discrepancy on same entity (e.g. port 8080 vs port 8000)
                num_a = set(re.findall(r"\b\d+\b", text_a))
                num_b = set(re.findall(r"\b\d+\b", text_b))
                num_discrepancy = bool(num_a and num_b and (num_a != num_b) and jaccard > 0.45)

                if has_polarity_clash or negation_clash or num_discrepancy:
                    severity = "CRITICAL" if has_polarity_clash else ("HIGH" if negation_clash else "MEDIUM")
                    
                    if has_polarity_clash and clash_pair:
                        rec = f"Polarity opposition detected on '{clash_pair[0]}' vs '{clash_pair[1]}'. Verify authoritative system configuration."
                    elif num_discrepancy:
                        rec = f"Numerical value mismatch ({', '.join(num_a)} vs {', '.join(num_b)}). Check timestamp recency to resolve."
                    else:
                        rec = "Negation conflict on shared subject context. Reconcile user preference or dialectic synthesis."

                    conflicts.append(
                        DialecticConflict(
                            thesis_id=id_a,
                            thesis_text=text_a,
                            antithesis_id=id_b,
                            antithesis_text=text_b,
                            conflict_topic=topic,
                            conflict_severity=severity,
                            similarity_context=round(jaccard, 3),
                            synthesis_recommendation=rec,
                        )
                    )

        return conflicts

    @classmethod
    def evaluate_feeling_of_knowing(
        cls,
        query: str,
        retrieved_memories: Sequence[Any],
        all_memories: Sequence[Any],
    ) -> MetacognitiveAuditResult:
        """Perform Feeling-of-Knowing (FOK) and Tip-of-the-Tongue (TOT) analysis for a query."""
        q_tokens = tokenize(query)
        q_set = set(q_tokens)

        # Recalled memories inspection
        recalled_scores: List[float] = []
        recalled_tokens: Set[str] = set()

        for rm in retrieved_memories:
            score = 0.5
            text = ""
            if isinstance(rm, dict):
                score = float(rm.get("similarity_score", rm.get("score", 0.5)))
                text = str(rm.get("text", ""))
            elif hasattr(rm, "score") and hasattr(rm, "text"):
                score = float(rm.score)
                text = str(rm.text)
            elif hasattr(rm, "text"):
                text = str(rm.text)

            recalled_scores.append(score)
            recalled_tokens.update(tokenize(text))

        entropy = cls.calculate_distribution_entropy(recalled_scores)
        top_score = max(recalled_scores) if recalled_scores else 0.0

        # Latent graph association scan (check if all_memories have synaptic / co-occurrence links)
        latent_hits: List[Tuple[str, float]] = []
        token_cooccurrence: Dict[str, int] = {}

        for m in all_memories:
            m_text = m.get("text", "") if isinstance(m, dict) else getattr(m, "text", "")
            m_id = m.get("id", "") if isinstance(m, dict) else getattr(m, "id", "")
            m_toks = set(tokenize(m_text))
            
            overlap = q_set.intersection(m_toks)
            if overlap:
                for t in m_toks:
                    if t not in q_set and t not in STOP_WORDS:
                        token_cooccurrence[t] = token_cooccurrence.get(t, 0) + 1
            if len(overlap) == 1 and len(q_set) > 1:
                latent_hits.append((m_id, len(overlap) / max(1, len(q_set))))

        latent_score = min(1.0, sum(s for _, s in latent_hits) / max(1, len(latent_hits))) if latent_hits else 0.0

        # Determine Epistemic State
        bridging_cues: List[str] = []
        if top_score >= 0.65 or (len(retrieved_memories) >= 2 and top_score >= 0.45):
            epistemic_state = "CONFIDENT_RECALL"
            certainty = round(top_score * (1.0 - entropy * 0.25), 3)
            summary = f"Confident epistemic recall: {len(retrieved_memories)} traces match query cues directly."
        elif latent_score > 0.20 or (token_cooccurrence and top_score > 0.15):
            epistemic_state = "TIP_OF_THE_TONGUE"
            certainty = round(0.35 + latent_score * 0.35, 3)
            # Find top bridging tokens
            sorted_bridges = sorted(token_cooccurrence.items(), key=lambda x: x[1], reverse=True)
            bridging_cues = [w for w, _ in sorted_bridges[:5]]
            summary = (
                f"Tip-of-the-Tongue state: Latent synaptic associations detected ({latent_score:.2f}), "
                f"but direct lexical surface match is low. Recommended bridging cues: {', '.join(bridging_cues[:3])}."
            )
        else:
            epistemic_state = "EPISTEMIC_GAP"
            certainty = round(top_score * 0.4, 3)
            summary = "Epistemic void: No significant direct recall or latent synaptic traces found for query."

        # Detect conflicts among retrieved memories
        conflicts = cls.detect_conflicts(retrieved_memories)

        # Source attributions
        attributions: List[SourceProvenance] = []
        for rm in retrieved_memories:
            m_id = rm.get("id", "") if isinstance(rm, dict) else getattr(rm, "id", "")
            m_text = rm.get("text", "") if isinstance(rm, dict) else getattr(rm, "text", "")
            meta = rm.get("metadata", {}) if isinstance(rm, dict) else getattr(rm, "metadata", {})
            attributions.append(cls.evaluate_source_provenance(m_id, m_text, meta))

        return MetacognitiveAuditResult(
            query=query,
            epistemic_state=epistemic_state,
            certainty_score=max(0.0, min(1.0, certainty)),
            retrieval_entropy=entropy,
            recalled_count=len(retrieved_memories),
            latent_association_score=round(latent_score, 3),
            bridging_cues=bridging_cues,
            conflicts_detected=conflicts,
            source_attributions=attributions,
            summary=summary,
        )


def audit_metacognition(
    daemon_or_storage: Any,
    query: str = "",
    top_k: int = 5,
) -> Dict[str, Any]:
    """Unified high-level entrypoint for MCP, REST, and CLI metacognitive evaluation."""
    # Retrieve memories depending on backend type
    if hasattr(daemon_or_storage, "recall") and callable(daemon_or_storage.recall):
        retrieved = daemon_or_storage.recall(query=query, top_k=top_k) if query else []
        all_memories = list(daemon_or_storage.nodes.values()) if hasattr(daemon_or_storage, "nodes") else []
    elif hasattr(daemon_or_storage, "list_memories") and callable(daemon_or_storage.list_memories):
        all_memories = daemon_or_storage.list_memories(limit=200)
        retrieved = daemon_or_storage.search_text(query, limit=top_k) if query else all_memories[:top_k]
    else:
        retrieved = []
        all_memories = []

    result = MetacognitiveEvaluator.evaluate_feeling_of_knowing(
        query=query,
        retrieved_memories=retrieved,
        all_memories=all_memories,
    )
    return result.to_dict()
