"""
Mapping engine orchestrator.
Combines rule-based (Layer 1) and LLM-based (Layer 2) mapping.
"""

from app.models.schemas import Finding, MASVSMapping
from app.mapping.rules import RuleMapper
from app.mapping.llm_mapper import llm_map_finding
from app.core.logging import get_logger

logger = get_logger(__name__)

LLM_CONFIDENCE_THRESHOLD = 0.7


class MappingEngine:
    """
    Two-layer MASVS/MASWE/MASTG mapping engine.
    Layer 1: Rule-based fast matching
    Layer 2: LLM semantic fallback for low-confidence results
    """

    def __init__(self, rules_path: str | None = None):
        self.rule_mapper = RuleMapper(rules_path)

    def map_finding_rules_only(self, finding: Finding) -> Finding:
        """Map using only rules (no LLM). Used in demo/offline mode."""
        mapping = self.rule_mapper.map_finding(finding)
        finding.masvs_mapping = mapping
        return finding

    async def map_finding(self, finding: Finding, gemini_client=None) -> Finding:
        """
        Map a finding using rules first, then LLM fallback if needed.

        Args:
            finding: Finding to map
            gemini_client: Optional Gemini client for LLM mapping

        Returns:
            Finding enriched with MASVS mapping
        """
        # Layer 1: Rule-based mapping
        rule_mapping = self.rule_mapper.map_finding(finding)

        if rule_mapping.confidence >= LLM_CONFIDENCE_THRESHOLD:
            finding.masvs_mapping = rule_mapping
            return finding

        # Layer 2: LLM fallback (if client available)
        if gemini_client is not None:
            llm_mapping = await llm_map_finding(finding, gemini_client)

            if llm_mapping.confidence > rule_mapping.confidence:
                # Merge: LLM mapping with any additional rule IDs
                merged = MASVSMapping(
                    maswe_ids=list(set(llm_mapping.maswe_ids + rule_mapping.maswe_ids)),
                    masvs_ids=list(set(llm_mapping.masvs_ids + rule_mapping.masvs_ids)),
                    mastg_tests=list(set(llm_mapping.mastg_tests + rule_mapping.mastg_tests)),
                    confidence=max(llm_mapping.confidence, rule_mapping.confidence),
                    rationale=f"LLM: {llm_mapping.rationale}; Rules: {rule_mapping.rationale}",
                    mapping_source="llm+rule",
                )
                finding.masvs_mapping = merged
            else:
                finding.masvs_mapping = rule_mapping
        else:
            finding.masvs_mapping = rule_mapping

        return finding

    async def map_findings(self, findings: list[Finding], gemini_client=None) -> list[Finding]:
        """Map multiple findings."""
        for finding in findings:
            await self.map_finding(finding, gemini_client)
        return findings

    def map_findings_rules_only(self, findings: list[Finding]) -> list[Finding]:
        """Map multiple findings using only rules (synchronous)."""
        for finding in findings:
            self.map_finding_rules_only(finding)
        return findings
