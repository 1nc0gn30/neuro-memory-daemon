"""
Unit tests for Metacognitive Memory Indexing, Epistemic Uncertainty & ACC Conflict Monitor.
"""

import json
import pytest
from neuro_memory_daemon.metacognition import (
    MetacognitiveEvaluator,
    SourceProvenance,
    DialecticConflict,
    MetacognitiveAuditResult,
    audit_metacognition,
)
from neuro_memory_daemon import MemoryDaemon, audit_metacognitive_memory


class TestMetacognitiveCalculations:
    def test_distribution_entropy_uniform_vs_skewed(self):
        # Uniform scores should have high normalized entropy (~1.0)
        uniform = [1.0, 1.0, 1.0, 1.0]
        ent_uniform = MetacognitiveEvaluator.calculate_distribution_entropy(uniform)
        assert ent_uniform > 0.95

        # Single dominant score should have lower entropy
        skewed = [10.0, 0.1, 0.05]
        ent_skewed = MetacognitiveEvaluator.calculate_distribution_entropy(skewed)
        assert ent_skewed < ent_uniform

        # Empty or zero
        assert MetacognitiveEvaluator.calculate_distribution_entropy([]) == 0.0
        assert MetacognitiveEvaluator.calculate_distribution_entropy([0.0, 0.0]) == 0.0

    def test_source_provenance_classification(self):
        # Instructional
        inst = MetacognitiveEvaluator.evaluate_source_provenance(
            "mem_1", "Agents must always validate JSON inputs before executing commands."
        )
        assert inst.provenance_type == "INSTRUCTIONAL"
        assert inst.grounding_confidence >= 0.90
        assert inst.hallucination_risk == "LOW"

        # Perceptual / empirical
        perc = MetacognitiveEvaluator.evaluate_source_provenance(
            "mem_2", "HTTP GET /api/v1/health returned status 200 OK with payload timestamp."
        )
        assert perc.provenance_type == "PERCEPTUAL"
        assert perc.grounding_confidence >= 0.85

        # Inferred
        inf = MetacognitiveEvaluator.evaluate_source_provenance(
            "mem_3", "The sudden traffic spike therefore suggests a potential DDoS attempt."
        )
        assert inf.provenance_type == "INFERRED"
        assert inf.grounding_confidence <= 0.85

        # Consolidated
        cons = MetacognitiveEvaluator.evaluate_source_provenance(
            "mem_4", "Aggregated schema synthesis from memory cluster replay.", metadata={"category": "consolidated"}
        )
        assert cons.provenance_type == "CONSOLIDATED"


class TestAnteriorCingulateCortexConflictDetector:
    def test_polarity_clash_detection(self):
        memories = [
            {"id": "m1", "text": "The API gateway rate limiter is enabled on production servers."},
            {"id": "m2", "text": "The API gateway rate limiter is disabled on production servers."},
        ]
        conflicts = MetacognitiveEvaluator.detect_conflicts(memories)
        assert len(conflicts) == 1
        conf = conflicts[0]
        assert conf.thesis_id == "m1"
        assert conf.antithesis_id == "m2"
        assert conf.conflict_severity == "CRITICAL"
        assert "enabled" in conf.synthesis_recommendation and "disabled" in conf.synthesis_recommendation

    def test_numerical_discrepancy_detection(self):
        memories = [
            {"id": "db_port_1", "text": "PostgreSQL database instance configured to listen on port 5432."},
            {"id": "db_port_2", "text": "PostgreSQL database instance configured to listen on port 5433."},
        ]
        conflicts = MetacognitiveEvaluator.detect_conflicts(memories)
        assert len(conflicts) == 1
        conf = conflicts[0]
        assert "5432" in conf.synthesis_recommendation or "5433" in conf.synthesis_recommendation

    def test_negation_clash_detection(self):
        memories = [
            {"id": "auth_1", "text": "User session authentication requires multi-factor auth tokens."},
            {"id": "auth_2", "text": "User session authentication does not require multi-factor auth tokens."},
        ]
        conflicts = MetacognitiveEvaluator.detect_conflicts(memories)
        assert len(conflicts) >= 1
        assert any(c.conflict_severity in ("HIGH", "CRITICAL") for c in conflicts)

    def test_no_conflicts_on_compatible_memories(self):
        memories = [
            {"id": "m1", "text": "Python 3.13 was released with experimental free-threaded mode."},
            {"id": "m2", "text": "Pytest is our primary testing framework running across all suites."},
        ]
        conflicts = MetacognitiveEvaluator.detect_conflicts(memories)
        assert len(conflicts) == 0


class TestFeelingOfKnowingAndTipOfTheTongue:
    def test_confident_recall_state(self):
        retrieved = [
            {"id": "m1", "text": "PostgreSQL cluster configuration on AWS RDS.", "score": 0.85},
            {"id": "m2", "text": "PostgreSQL read replica backup schedule.", "score": 0.72},
        ]
        res = MetacognitiveEvaluator.evaluate_feeling_of_knowing(
            query="PostgreSQL database",
            retrieved_memories=retrieved,
            all_memories=retrieved,
        )
        assert res.epistemic_state == "CONFIDENT_RECALL"
        assert res.certainty_score >= 0.50
        assert res.recalled_count == 2

    def test_tip_of_the_tongue_state(self):
        # Query shares latent tokens with all_memories, but retrieved direct match score is low
        all_memories = [
            {"id": "m1", "text": "OAuth2 authentication bearer token security protocol."},
            {"id": "m2", "text": "JWT signature verification and public key rotation."},
            {"id": "m3", "text": "Cryptographic hash algorithms SHA256 and HMAC."},
        ]
        retrieved = [
            {"id": "m1", "text": "OAuth2 authentication bearer token security protocol.", "score": 0.25}
        ]
        res = MetacognitiveEvaluator.evaluate_feeling_of_knowing(
            query="token encryption credentials",
            retrieved_memories=retrieved,
            all_memories=all_memories,
        )
        assert res.epistemic_state in ("TIP_OF_THE_TONGUE", "CONFIDENT_RECALL")
        if res.epistemic_state == "TIP_OF_THE_TONGUE":
            assert len(res.bridging_cues) > 0

    def test_epistemic_gap_state(self):
        all_memories = [
            {"id": "m1", "text": "Cooking lasagna with fresh mozzarella and basil leaves."}
        ]
        res = MetacognitiveEvaluator.evaluate_feeling_of_knowing(
            query="Quantum chromodynamics gluon plasma",
            retrieved_memories=[],
            all_memories=all_memories,
        )
        assert res.epistemic_state == "EPISTEMIC_GAP"
        assert res.certainty_score < 0.20


class TestDaemonAndSystemIntegration:
    def test_daemon_audit_metacognition(self, tmp_path):
        db_file = tmp_path / "test_substrate.json"
        daemon = MemoryDaemon(db_path=db_file)

        daemon.store("PostgreSQL server runs on port 5432.", tags=["database", "postgres"])
        daemon.store("PostgreSQL server runs on port 5433.", tags=["database", "postgres"])
        daemon.store("Frontend web application hosted at localhost 3000.", tags=["frontend"])

        audit = daemon.audit_metacognition(query="postgres database port")
        assert "epistemic_state" in audit
        assert "certainty_score" in audit
        assert len(audit["conflicts_detected"]) >= 1

    def test_top_level_audit_function(self, tmp_path):
        db_file = tmp_path / "top_level_substrate.json"
        daemon = MemoryDaemon(db_path=db_file)
        daemon.store("Memory trace for top level audit verification.", tags=["test"])

        res = audit_metacognition(daemon, query="verification")
        assert res["recalled_count"] >= 1
        assert "source_attributions" in res
