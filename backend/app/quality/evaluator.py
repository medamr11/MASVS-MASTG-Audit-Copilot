"""
Quality evaluator — tracks mapping accuracy, dedup rates, and hallucination guards.
"""

import hashlib
import json
import re
from pathlib import Path

from app.models.schemas import EnrichedFinding
from app.core.logging import get_logger

logger = get_logger(__name__)

# Known valid MASVS/MASWE/MASTG IDs (subset for validation)
VALID_MASVS = {
    "MASVS-STORAGE-1", "MASVS-STORAGE-2", "MASVS-CRYPTO-1", "MASVS-CRYPTO-2",
    "MASVS-AUTH-1", "MASVS-AUTH-2", "MASVS-NETWORK-1", "MASVS-NETWORK-2",
    "MASVS-PLATFORM-1", "MASVS-PLATFORM-2", "MASVS-PLATFORM-3",
    "MASVS-CODE-1", "MASVS-CODE-4", "MASVS-RESILIENCE-1", "MASVS-RESILIENCE-2",
    "MASVS-RESILIENCE-3", "MASVS-PRIVACY-1", "MASVS-PRIVACY-2",
}


class QualityEvaluator:
    """Evaluate and track audit quality metrics."""

    def evaluate(self, findings: list[EnrichedFinding]) -> dict:
        """Produce a quality report for the audit."""
        total = len(findings)
        active = [f for f in findings if not f.is_duplicate]
        duplicates = [f for f in findings if f.is_duplicate]

        report = {
            "total_raw_findings": total,
            "unique_findings": len(active),
            "dedup_rate": f"{(len(duplicates) / total * 100):.1f}%" if total else "0%",
            "mapping_coverage": self._mapping_coverage(active),
            "hallucination_check": self._hallucination_check(active),
            "reproducibility_hash": self._compute_hash(findings),
            "score_distribution": self._score_distribution(active),
        }

        logger.info("quality_report", **report)
        return report

    def _mapping_coverage(self, findings: list[EnrichedFinding]) -> dict:
        """How many findings have MASVS mappings."""
        mapped = [f for f in findings if f.masvs_mapping and f.masvs_mapping.masvs_ids]
        high_conf = [f for f in mapped if f.masvs_mapping.confidence >= 0.7]

        return {
            "total": len(findings),
            "mapped": len(mapped),
            "high_confidence": len(high_conf),
            "coverage_pct": f"{(len(mapped) / len(findings) * 100):.1f}%" if findings else "0%",
        }

    def _hallucination_check(self, findings: list[EnrichedFinding]) -> dict:
        """Validate that all MASVS/MASTG IDs exist in the knowledge base."""
        invalid_ids = []
        for f in findings:
            if not f.masvs_mapping:
                continue
            for mid in f.masvs_mapping.masvs_ids:
                if mid not in VALID_MASVS and re.match(r"MASVS-\w+-\d+", mid):
                    invalid_ids.append(mid)

        return {
            "invalid_ids_found": len(invalid_ids),
            "invalid_ids": list(set(invalid_ids))[:10],
            "passed": len(invalid_ids) == 0,
        }

    def _compute_hash(self, findings: list[EnrichedFinding]) -> str:
        """Deterministic hash for reproducibility checking."""
        data = "|".join(
            f"{f.raw_title}:{f.severity.value}:{','.join(f.masvs_mapping.masvs_ids) if f.masvs_mapping else ''}"
            for f in sorted(findings, key=lambda x: x.raw_title)
        )
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _score_distribution(self, findings: list[EnrichedFinding]) -> dict:
        """Score distribution summary."""
        scores = [f.criticality_score for f in findings]
        if not scores:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}

        return {
            "min": min(scores),
            "max": max(scores),
            "avg": round(sum(scores) / len(scores), 2),
            "count": len(scores),
            "p1_count": len([s for s in scores if s >= 8.0]),
            "p2_count": len([s for s in scores if 6.0 <= s < 8.0]),
            "p3_count": len([s for s in scores if 4.0 <= s < 6.0]),
            "p4_count": len([s for s in scores if s < 4.0]),
        }
