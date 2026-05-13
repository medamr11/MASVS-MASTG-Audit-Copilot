"""
Unit tests for mapping engine.
"""

import pytest

from app.mapping.rules import RuleMapper
from app.mapping.engine import MappingEngine
from app.models.schemas import Finding, FindingSource, Severity, FindingCategory


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


class TestRuleMapper:
    def test_maps_hardcoded_secret(self):
        mapper = RuleMapper()
        finding = make_finding(
            raw_title="Hardcoded API Key",
            raw_description="Hardcoded secret API key found in source code",
            category=FindingCategory.CRYPTO,
        )
        result = mapper.map_finding(finding)
        assert result.confidence > 0
        assert any("MASVS-CRYPTO" in mid for mid in result.masvs_ids)

    def test_maps_cleartext(self):
        mapper = RuleMapper()
        finding = make_finding(
            raw_title="Cleartext HTTP Traffic",
            raw_description="Application uses http:// for API communication",
            category=FindingCategory.NETWORK,
        )
        result = mapper.map_finding(finding)
        assert result.confidence > 0
        assert any("MASVS-NETWORK" in mid for mid in result.masvs_ids)

    def test_maps_debuggable(self):
        mapper = RuleMapper()
        finding = make_finding(
            raw_title="Application is Debuggable",
            raw_description="The debuggable flag is set to true",
            category=FindingCategory.RESILIENCE,
        )
        result = mapper.map_finding(finding)
        assert result.confidence > 0.5

    def test_no_match_returns_zero_confidence(self):
        mapper = RuleMapper()
        finding = make_finding(
            raw_title="Something Unrelated",
            raw_description="Nothing to match here xyz123",
        )
        result = mapper.map_finding(finding)
        assert result.confidence == 0.0

    def test_maps_multiple_findings(self):
        mapper = RuleMapper()
        findings = [
            make_finding(raw_title="Hardcoded password", raw_description="password embedded"),
            make_finding(raw_title="DES cipher", raw_description="DES encryption used"),
        ]
        results = mapper.map_findings(findings)
        assert all(f.masvs_mapping is not None for f in results)


class TestMappingEngine:
    def test_rules_only_mode(self):
        engine = MappingEngine()
        finding = make_finding(
            raw_title="Hardcoded secret key",
            raw_description="API key hardcoded in the app",
            category=FindingCategory.CRYPTO,
        )
        result = engine.map_finding_rules_only(finding)
        assert result.masvs_mapping is not None
        assert result.masvs_mapping.mapping_source == "rule"

    def test_batch_rules_only(self):
        engine = MappingEngine()
        findings = [
            make_finding(raw_title="ECB mode", raw_description="ECB cipher detected"),
            make_finding(raw_title="SQL injection", raw_description="rawQuery with user input"),
        ]
        results = engine.map_findings_rules_only(findings)
        assert len(results) == 2
        assert all(f.masvs_mapping is not None for f in results)
