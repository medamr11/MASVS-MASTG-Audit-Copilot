"""
Rule-based MASVS/MASWE/MASTG mapper.
Layer 1: fast keyword + category matching against mapping_rules.json.
"""

import json
from pathlib import Path
from typing import Any

from app.models.schemas import Finding, MASVSMapping
from app.core.logging import get_logger

logger = get_logger(__name__)


class RuleMapper:
    """Keyword-based mapper using pre-built mapping rules."""

    def __init__(self, rules_path: str | Path | None = None):
        if rules_path is None:
            rules_path = Path(__file__).parent.parent.parent / "data" / "knowledge_base" / "mapping_rules.json"

        self.rules = self._load_rules(Path(rules_path))
        logger.info("rule_mapper_loaded", rule_count=len(self.rules))

    @staticmethod
    def _load_rules(path: Path) -> list[dict[str, Any]]:
        """Load mapping rules from JSON file."""
        if not path.exists():
            logger.warning("mapping_rules_not_found", path=str(path))
            return []
        with open(path) as f:
            data = json.load(f)
        return data.get("rules", [])

    def map_finding(self, finding: Finding) -> MASVSMapping:
        """Map a single finding using keyword matching."""
        best_match: dict[str, Any] | None = None
        best_score = 0.0

        search_text = f"{finding.raw_title} {finding.raw_description} {' '.join(finding.evidence[:3])}".lower()
        finding_category = finding.category.value.lower()

        for rule in self.rules:
            keywords = rule.get("keywords", [])
            rule_category = rule.get("category", "").lower()

            # Keyword matching score
            keyword_hits = sum(1 for kw in keywords if kw.lower() in search_text)
            if keyword_hits == 0:
                continue

            keyword_score = keyword_hits / len(keywords)

            # Category bonus
            category_bonus = 0.2 if self._category_match(finding_category, rule_category) else 0.0

            # Combined score
            total_score = (keyword_score * 0.8 + category_bonus) * rule.get("confidence", 0.5)

            if total_score > best_score:
                best_score = total_score
                best_match = rule

        if best_match and best_score > 0.1:
            return MASVSMapping(
                maswe_ids=best_match.get("maswe_ids", []),
                masvs_ids=best_match.get("masvs_ids", []),
                mastg_tests=best_match.get("mastg_tests", []),
                confidence=min(best_score, best_match.get("confidence", 0.5)),
                rationale=f"Matched keywords: {', '.join(best_match.get('keywords', [])[:5])}",
                mapping_source="rule",
            )

        return MASVSMapping(confidence=0.0, mapping_source="rule")

    def map_findings(self, findings: list[Finding]) -> list[Finding]:
        """Map multiple findings, enriching each with MASVS data."""
        for finding in findings:
            mapping = self.map_finding(finding)
            finding.masvs_mapping = mapping
        return findings

    @staticmethod
    def _category_match(finding_cat: str, rule_cat: str) -> bool:
        """Fuzzy category matching."""
        aliases = {
            "cryptography": ["crypto", "cryptography", "encryption", "cipher"],
            "network": ["network", "tls", "ssl", "http"],
            "storage": ["storage", "data", "file"],
            "platform": ["platform", "ipc", "component", "intent"],
            "authentication": ["auth", "authentication", "authorization", "session"],
            "code": ["code", "injection", "quality"],
            "resilience": ["resilience", "reverse", "tamper", "debug"],
            "privacy": ["privacy", "tracking", "permission"],
        }
        for canonical, aliases_list in aliases.items():
            if finding_cat in aliases_list and rule_cat in aliases_list:
                return True
        return finding_cat == rule_cat
