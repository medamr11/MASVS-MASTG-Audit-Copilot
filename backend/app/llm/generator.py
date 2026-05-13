"""
Report generator — LLM-powered deduplication, summaries, and remediation.
"""

import json
from typing import Any

from app.models.schemas import (
    ScoredFinding, EnrichedFinding, RemediationBlock,
    CategoryCoverage, CoverageMatrix, FindingCategory, Severity
)
from app.llm.client import GeminiClient
from app.llm.prompts import (
    DEDUP_SYSTEM, DEDUP_USER,
    EXEC_SUMMARY_SYSTEM, EXEC_SUMMARY_USER,
    REMEDIATION_SYSTEM, REMEDIATION_USER,
)
from app.rag.retriever import KnowledgeBaseRetriever
from app.core.logging import get_logger

logger = get_logger(__name__)

# MASVS categories with approximate control counts
MASVS_CATEGORIES = {
    "MASVS-STORAGE": {"name": "Data Storage", "total_controls": 2},
    "MASVS-CRYPTO": {"name": "Cryptography", "total_controls": 2},
    "MASVS-AUTH": {"name": "Authentication", "total_controls": 2},
    "MASVS-NETWORK": {"name": "Network Communication", "total_controls": 2},
    "MASVS-PLATFORM": {"name": "Platform Interaction", "total_controls": 3},
    "MASVS-CODE": {"name": "Code Quality", "total_controls": 2},
    "MASVS-RESILIENCE": {"name": "Resilience", "total_controls": 3},
    "MASVS-PRIVACY": {"name": "Privacy", "total_controls": 2},
}


class ReportGenerator:
    """LLM-powered report generation engine."""

    def __init__(self, gemini_client: GeminiClient | None = None,
                 retriever: KnowledgeBaseRetriever | None = None):
        self.llm = gemini_client
        self.retriever = retriever

    # ── Deduplication ────────────────────────────────────────────

    async def deduplicate(self, findings: list[ScoredFinding]) -> list[EnrichedFinding]:
        """Deduplicate findings using LLM or simple heuristics."""
        enriched = [EnrichedFinding(**f.model_dump()) for f in findings]

        if not self.llm or not self.llm.is_available or len(findings) <= 1:
            return enriched

        try:
            # Build findings text for LLM
            findings_text = "\n".join(
                f"- ID: {f.id[:8]} | Title: {f.raw_title} | Severity: {f.severity.value} | Source: {f.source.value}"
                for f in findings[:50]  # Cap at 50 to avoid token limits
            )

            prompt = DEDUP_USER.format(findings_text=findings_text)
            response = await self.llm.send_message(prompt, DEDUP_SYSTEM, max_tokens=2000)

            # Parse duplicate groups
            groups = json.loads(response) if isinstance(response, str) else response
            if not isinstance(groups, list):
                return enriched

            # Process duplicate groups
            id_map = {f.id[:8]: f for f in enriched}
            for group in groups:
                group_id = group.get("group_id", "")
                member_ids = group.get("finding_ids", [])
                if len(member_ids) < 2:
                    continue

                # Mark duplicates
                primary = None
                for mid in member_ids:
                    for eid, ef in id_map.items():
                        if eid.startswith(mid[:6]):
                            ef.duplicate_group_id = group_id
                            if primary is None:
                                primary = ef
                            else:
                                ef.is_duplicate = True

            logger.info("dedup_complete", groups=len(groups))

        except Exception as e:
            logger.error("dedup_failed", error=str(e))

        return enriched

    # ── Executive Summary ────────────────────────────────────────

    async def generate_executive_summary(
        self,
        app_name: str,
        app_package: str,
        audit_date: str,
        platform: str,
        findings: list[EnrichedFinding],
        coverage: CoverageMatrix,
    ) -> str:
        """Generate CISO-audience executive summary."""
        if not self.llm or not self.llm.is_available:
            return self._fallback_executive_summary(app_name, findings, coverage)

        # Count severities
        counts = {s: 0 for s in Severity}
        for f in findings:
            if not f.is_duplicate:
                counts[f.severity] = counts.get(f.severity, 0) + 1

        # Top findings text
        active = [f for f in findings if not f.is_duplicate]
        top = sorted(active, key=lambda f: f.criticality_score, reverse=True)[:10]
        top_text = "\n".join(
            f"- [{f.priority.value}] {f.raw_title} (Score: {f.criticality_score}, Severity: {f.severity.value})"
            for f in top
        )

        # Coverage text
        cov_text = "\n".join(
            f"- {c.category}: {c.failed} failed, {c.passed} passed, {c.not_tested} not tested"
            for c in coverage.categories
        )

        prompt = EXEC_SUMMARY_USER.format(
            app_name=app_name,
            app_package=app_package,
            audit_date=audit_date,
            platform=platform,
            overall_score=f"{coverage.overall_score:.1f}",
            total_findings=len(active),
            critical_count=counts.get(Severity.CRITICAL, 0),
            high_count=counts.get(Severity.HIGH, 0),
            medium_count=counts.get(Severity.MEDIUM, 0),
            low_count=counts.get(Severity.LOW, 0),
            coverage_text=cov_text or "N/A",
            top_findings=top_text or "None",
        )

        try:
            summary = await self.llm.send_message(prompt, EXEC_SUMMARY_SYSTEM, max_tokens=1500)
            return summary.strip()
        except Exception as e:
            logger.error("exec_summary_failed", error=str(e))
            return self._fallback_executive_summary(app_name, findings, coverage)

    # ── Per-Finding Remediation ──────────────────────────────────

    async def generate_remediation(self, finding: EnrichedFinding) -> RemediationBlock:
        """Generate RAG-augmented remediation for a finding."""
        # Get RAG context
        rag_context = ""
        if self.retriever:
            masvs_ids = finding.masvs_mapping.masvs_ids if finding.masvs_mapping else []
            rag_context = self.retriever.retrieve_for_finding(
                finding.raw_title, finding.raw_description, masvs_ids, k=3
            )

        if not self.llm or not self.llm.is_available:
            return self._fallback_remediation(finding, rag_context)

        try:
            prompt = REMEDIATION_USER.format(
                title=finding.raw_title,
                description=finding.raw_description[:500],
                severity=finding.severity.value,
                category=finding.category.value,
                evidence=" | ".join(finding.evidence[:2])[:300],
                masvs_ids=", ".join(finding.masvs_mapping.masvs_ids) if finding.masvs_mapping else "N/A",
                rag_context=rag_context[:2000],
            )

            result = await self.llm.send_json_message(prompt, REMEDIATION_SYSTEM, max_tokens=1000)

            return RemediationBlock(
                short_fix=result.get("short_fix", "Review and remediate this finding."),
                detailed_steps=result.get("detailed_steps", []),
                code_example=result.get("code_example"),
                references=result.get("references", []),
            )
        except Exception as e:
            logger.error("remediation_failed", finding_id=finding.id, error=str(e))
            return self._fallback_remediation(finding, rag_context)

    # ── Coverage Matrix ──────────────────────────────────────────

    def compute_coverage_matrix(self, findings: list[EnrichedFinding]) -> CoverageMatrix:
        """Compute MASVS coverage from findings."""
        categories = []
        total_score = 0.0

        for cat_id, cat_info in MASVS_CATEGORIES.items():
            # Find findings for this category
            cat_findings = [
                f for f in findings
                if not f.is_duplicate and f.masvs_mapping
                and any(cat_id in mid for mid in f.masvs_mapping.masvs_ids)
            ]

            tested = len(cat_findings)
            failed = len([f for f in cat_findings
                         if f.severity.value in ("critical", "high", "medium")])
            passed = tested - failed
            total = cat_info["total_controls"]
            not_tested = max(0, total - tested)

            # Score: higher is better (fewer failures)
            if tested > 0:
                score = round(((passed / tested) * 10), 1) if tested > 0 else 5.0
            else:
                score = 5.0  # Untested = neutral

            categories.append(CategoryCoverage(
                category=cat_id,
                total_controls=total,
                tested=tested,
                passed=passed,
                failed=failed,
                not_tested=not_tested,
                score=score,
            ))
            total_score += score

        overall = round(total_score / len(MASVS_CATEGORIES), 1) if MASVS_CATEGORIES else 0.0

        return CoverageMatrix(categories=categories, overall_score=overall)

    # ── Fallbacks ────────────────────────────────────────────────

    @staticmethod
    def _fallback_executive_summary(app_name: str, findings: list, coverage: CoverageMatrix) -> str:
        active = [f for f in findings if not getattr(f, "is_duplicate", False)]
        critical = len([f for f in active if f.severity == Severity.CRITICAL])
        high = len([f for f in active if f.severity == Severity.HIGH])

        return (
            f"A security assessment of {app_name} identified {len(active)} unique findings. "
            f"Of these, {critical} are rated Critical and {high} are rated High severity. "
            f"The overall MASVS compliance score is {coverage.overall_score:.1f}/10.0. "
            f"Immediate attention is recommended for all Critical and High severity findings "
            f"to reduce the application's attack surface."
        )

    @staticmethod
    def _fallback_remediation(finding, rag_context: str) -> RemediationBlock:
        return RemediationBlock(
            short_fix=f"Review and remediate: {finding.raw_title}",
            detailed_steps=[
                f"Investigate the {finding.category.value} issue: {finding.raw_title}",
                f"Review evidence and confirm the finding",
                f"Apply appropriate fix based on MASVS guidelines",
                f"Test the fix and verify remediation",
            ],
            code_example=None,
            references=[],
        )
