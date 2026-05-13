"""
Criticality scoring engine.
Score = (Impact × Exploitability × Exposure) / normalization_factor
"""

import json
from app.models.schemas import (
    Finding, ScoredFinding, Severity, FindingCategory, Priority, MASVSLevel
)
from app.core.logging import get_logger

logger = get_logger(__name__)

NORMALIZATION_FACTOR = 12.5  # max(5*5*5) / 10 = 12.5


class ScoringEngine:
    """Compute criticality scores for findings."""

    # Default score heuristics based on severity
    SEVERITY_DEFAULTS = {
        Severity.CRITICAL: {"impact": 5, "exploitability": 4, "exposure": 4},
        Severity.HIGH:     {"impact": 4, "exploitability": 3, "exposure": 3},
        Severity.MEDIUM:   {"impact": 3, "exploitability": 3, "exposure": 3},
        Severity.LOW:      {"impact": 2, "exploitability": 2, "exposure": 2},
        Severity.INFO:     {"impact": 1, "exploitability": 1, "exposure": 1},
    }

    # Category-specific score adjustments
    CATEGORY_ADJUSTMENTS = {
        FindingCategory.CRYPTO: {"impact": 1},      # Crypto issues often have high impact
        FindingCategory.AUTH: {"impact": 1},          # Auth issues are impactful
        FindingCategory.NETWORK: {"exposure": 1},     # Network issues have high exposure
        FindingCategory.STORAGE: {"impact": 0},
        FindingCategory.PLATFORM: {"exploitability": 0},
        FindingCategory.CODE: {"exploitability": 0},
        FindingCategory.RESILIENCE: {"exploitability": -1},  # Requires reverse engineering
        FindingCategory.PRIVACY: {"impact": 0},
    }

    # Keyword-based score refinements
    KEYWORD_SCORES = {
        "credential": {"impact": 5},
        "password": {"impact": 5},
        "api_key": {"impact": 4},
        "token": {"impact": 4},
        "pii": {"impact": 4},
        "personal": {"impact": 4},
        "internet-facing": {"exposure": 5},
        "remote": {"exposure": 4},
        "local": {"exposure": 2},
        "physical": {"exploitability": 1},
        "no prerequisite": {"exploitability": 5},
        "root": {"exploitability": 2},
        "mitm": {"exploitability": 4, "exposure": 5},
        "command execution": {"impact": 5, "exploitability": 4},
        "debuggable": {"exploitability": 4},
        "cleartext": {"exposure": 4},
    }

    # MASVS level mapping by category
    CATEGORY_LEVEL_MAP = {
        FindingCategory.STORAGE: MASVSLevel.L1,
        FindingCategory.CRYPTO: MASVSLevel.L1,
        FindingCategory.AUTH: MASVSLevel.L1,
        FindingCategory.NETWORK: MASVSLevel.L1,
        FindingCategory.PLATFORM: MASVSLevel.L1,
        FindingCategory.CODE: MASVSLevel.L1,
        FindingCategory.RESILIENCE: MASVSLevel.R,
        FindingCategory.PRIVACY: MASVSLevel.L2,
    }

    def score_finding(self, finding: Finding) -> ScoredFinding:
        """Score a single finding using heuristic rules."""
        # Start with severity defaults
        defaults = self.SEVERITY_DEFAULTS.get(
            finding.severity, self.SEVERITY_DEFAULTS[Severity.INFO]
        )
        impact = defaults["impact"]
        exploitability = defaults["exploitability"]
        exposure = defaults["exposure"]

        # Apply category adjustments
        adj = self.CATEGORY_ADJUSTMENTS.get(finding.category, {})
        impact = self._clamp(impact + adj.get("impact", 0))
        exploitability = self._clamp(exploitability + adj.get("exploitability", 0))
        exposure = self._clamp(exposure + adj.get("exposure", 0))

        # Apply keyword refinements
        search_text = f"{finding.raw_title} {finding.raw_description}".lower()
        for keyword, scores in self.KEYWORD_SCORES.items():
            if keyword in search_text:
                if "impact" in scores:
                    impact = max(impact, scores["impact"])
                if "exploitability" in scores:
                    exploitability = max(exploitability, scores["exploitability"])
                if "exposure" in scores:
                    exposure = max(exposure, scores["exposure"])

        # Compute criticality score
        raw_score = (impact * exploitability * exposure) / NORMALIZATION_FACTOR
        criticality_score = round(min(raw_score, 10.0), 1)

        # Determine priority
        priority = self._score_to_priority(criticality_score)

        # Determine MASVS level
        masvs_level = self.CATEGORY_LEVEL_MAP.get(finding.category, MASVSLevel.L1)

        # Confidence based on how much signal we had
        confidence = 0.6 if finding.severity == Severity.INFO else 0.75

        return ScoredFinding(
            **finding.model_dump(),
            impact=impact,
            exploitability=exploitability,
            exposure=exposure,
            criticality_score=criticality_score,
            priority=priority,
            masvs_level=masvs_level,
            score_confidence=confidence,
        )

    def score_findings(self, findings: list[Finding]) -> list[ScoredFinding]:
        """Score multiple findings."""
        scored = []
        for finding in findings:
            try:
                scored.append(self.score_finding(finding))
            except Exception as e:
                logger.error("scoring_error", finding_id=finding.id, error=str(e))
                # Return with default scores
                scored.append(ScoredFinding(**finding.model_dump()))
        return scored

    async def score_finding_with_llm(self, finding: Finding, claude_client) -> ScoredFinding:
        """Score using LLM for ambiguous findings. Falls back to heuristic."""
        scored = self.score_finding(finding)

        if scored.score_confidence < 0.7 and claude_client:
            try:
                prompt = f"""Score this mobile security finding on three dimensions (1-5 each):

Finding: {finding.raw_title}
Description: {finding.raw_description[:500]}
Severity: {finding.severity.value}
Category: {finding.category.value}

Dimensions:
- Impact: data sensitivity (credentials=5, PII=4, app state=3, UX=2, cosmetic=1)
- Exploitability: attacker prerequisite (no prereq=5, local=3, physical=1)
- Exposure: attack surface (internet-facing=5, LAN=3, local IPC=2, static only=1)

Respond ONLY with JSON: {{"impact": N, "exploitability": N, "exposure": N}}"""

                response = await claude_client.send_message(
                    system_prompt="You are a mobile security scoring expert. Respond only with JSON.",
                    user_prompt=prompt,
                    max_tokens=100,
                )
                result = json.loads(response)
                scored.impact = self._clamp(result.get("impact", scored.impact))
                scored.exploitability = self._clamp(result.get("exploitability", scored.exploitability))
                scored.exposure = self._clamp(result.get("exposure", scored.exposure))

                raw = (scored.impact * scored.exploitability * scored.exposure) / NORMALIZATION_FACTOR
                scored.criticality_score = round(min(raw, 10.0), 1)
                scored.priority = self._score_to_priority(scored.criticality_score)
                scored.score_confidence = 0.9

            except Exception as e:
                logger.error("llm_scoring_failed", finding_id=finding.id, error=str(e))

        return scored

    @staticmethod
    def _clamp(value: int, low: int = 1, high: int = 5) -> int:
        return max(low, min(high, value))

    @staticmethod
    def _score_to_priority(score: float) -> Priority:
        if score >= 8.0:
            return Priority.P1
        elif score >= 6.0:
            return Priority.P2
        elif score >= 4.0:
            return Priority.P3
        return Priority.P4
