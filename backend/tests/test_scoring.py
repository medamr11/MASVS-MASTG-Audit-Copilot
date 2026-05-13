"""
Unit tests for scoring engine.
"""

import pytest

from app.scoring.engine import ScoringEngine
from app.models.schemas import Finding, FindingSource, Severity, FindingCategory, Priority


def make_finding(**kwargs) -> Finding:
    defaults = {
        "source": FindingSource.MOBSF,
        "raw_title": "Test Finding",
        "raw_description": "Test description",
        "severity": Severity.MEDIUM,
        "category": FindingCategory.OTHER,
    }
    defaults.update(kwargs)
    return Finding(**defaults)


class TestScoringEngine:
    def setup_method(self):
        self.engine = ScoringEngine()

    def test_critical_gets_high_score(self):
        finding = make_finding(
            severity=Severity.CRITICAL,
            raw_title="Hardcoded password",
            raw_description="Password credential found in source code",
        )
        scored = self.engine.score_finding(finding)
        assert scored.criticality_score >= 6.0
        assert scored.priority in (Priority.P1, Priority.P2)

    def test_info_gets_low_score(self):
        finding = make_finding(
            severity=Severity.INFO,
            raw_title="Information disclosure",
            raw_description="Minor info about app version",
        )
        scored = self.engine.score_finding(finding)
        assert scored.criticality_score < 4.0
        assert scored.priority == Priority.P4

    def test_network_gets_exposure_boost(self):
        finding = make_finding(
            severity=Severity.HIGH,
            category=FindingCategory.NETWORK,
            raw_title="Cleartext HTTP traffic",
            raw_description="App uses cleartext HTTP",
        )
        scored = self.engine.score_finding(finding)
        assert scored.exposure >= 3

    def test_resilience_lower_exploitability(self):
        finding = make_finding(
            severity=Severity.MEDIUM,
            category=FindingCategory.RESILIENCE,
            raw_title="Missing obfuscation",
            raw_description="Code is not obfuscated",
        )
        scored = self.engine.score_finding(finding)
        assert scored.exploitability <= 3

    def test_score_range(self):
        finding = make_finding(severity=Severity.HIGH)
        scored = self.engine.score_finding(finding)
        assert 0.0 <= scored.criticality_score <= 10.0
        assert 1 <= scored.impact <= 5
        assert 1 <= scored.exploitability <= 5
        assert 1 <= scored.exposure <= 5

    def test_batch_scoring(self):
        findings = [
            make_finding(severity=Severity.CRITICAL),
            make_finding(severity=Severity.LOW),
            make_finding(severity=Severity.INFO),
        ]
        scored = self.engine.score_findings(findings)
        assert len(scored) == 3
        assert scored[0].criticality_score >= scored[2].criticality_score

    def test_mitm_keyword_boost(self):
        finding = make_finding(
            severity=Severity.HIGH,
            raw_title="Certificate bypass enables MITM",
            raw_description="TrustAll allows man-in-the-middle attacks",
        )
        scored = self.engine.score_finding(finding)
        assert scored.exposure >= 4

    def test_priority_thresholds(self):
        assert ScoringEngine._score_to_priority(9.0) == Priority.P1
        assert ScoringEngine._score_to_priority(7.0) == Priority.P2
        assert ScoringEngine._score_to_priority(5.0) == Priority.P3
        assert ScoringEngine._score_to_priority(2.0) == Priority.P4
