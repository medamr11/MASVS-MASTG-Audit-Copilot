"""
Analysis pipeline orchestrator.
Manages the full audit workflow: Parse → Map → Score → Dedup → LLM → Report
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator

from app.models.schemas import (
    AppMetadata, EnrichedFinding, Finding, ScoredFinding,
    PipelineEvent, JobStatus, CoverageMatrix,
)
from app.parsers.normalizer import FindingNormalizer
from app.mapping.engine import MappingEngine
from app.scoring.engine import ScoringEngine
from app.llm.client import GeminiClient
from app.llm.generator import ReportGenerator
from app.rag.retriever import KnowledgeBaseRetriever
from app.report.html_generator import HTMLReportGenerator
from app.report.pdf_generator import PDFReportGenerator
from app.report.json_generator import JSONReportGenerator
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalysisPipeline:
    """Orchestrates the full MASVS audit pipeline."""

    def __init__(self, use_llm: bool = True):
        self.settings = get_settings()
        self.normalizer = FindingNormalizer()
        self.mapper = MappingEngine()
        self.scorer = ScoringEngine()
        self.html_gen = HTMLReportGenerator()
        self.pdf_gen = PDFReportGenerator()
        self.json_gen = JSONReportGenerator()

        # LLM + RAG (optional)
        self.gemini = None
        self.retriever = None
        self.report_gen = None

        if use_llm and self.settings.gemini_api_key:
            self.gemini = GeminiClient()
            try:
                self.retriever = KnowledgeBaseRetriever()
            except Exception:
                logger.warning("retriever_init_failed")
            self.report_gen = ReportGenerator(self.gemini, self.retriever)
        else:
            self.report_gen = ReportGenerator(None, None)

    async def run(
        self,
        file_paths: list[str | Path],
        app_metadata: AppMetadata,
        job_id: str | None = None,
    ) -> AsyncGenerator[PipelineEvent, None]:
        """
        Run the full pipeline, yielding SSE events at each stage.

        Args:
            file_paths: Paths to uploaded artifact files
            app_metadata: Application metadata
            job_id: Optional job ID

        Yields:
            PipelineEvent objects for SSE streaming
        """
        job_id = job_id or str(uuid.uuid4())
        results: dict[str, Any] = {"job_id": job_id}

        try:
            # ── Stage 1: Parsing ─────────────────────────────────
            yield PipelineEvent(
                event_type="stage_update", stage="parsing",
                progress=0.1, message="Parsing uploaded artifacts..."
            )

            findings = self.normalizer.normalize_multiple(file_paths)
            results["raw_findings"] = findings

            yield PipelineEvent(
                event_type="stage_update", stage="parsing",
                progress=0.2, message=f"Parsed {len(findings)} raw findings",
                finding_count=len(findings)
            )

            # ── Stage 2: Mapping ─────────────────────────────────
            yield PipelineEvent(
                event_type="stage_update", stage="mapping",
                progress=0.3, message="Mapping findings to MASVS controls..."
            )

            if self.gemini and self.gemini.is_available:
                findings = await self.mapper.map_findings(findings, self.gemini)
            else:
                findings = self.mapper.map_findings_rules_only(findings)

            yield PipelineEvent(
                event_type="stage_update", stage="mapping",
                progress=0.4, message="MASVS mapping complete",
                finding_count=len(findings)
            )

            # ── Stage 3: Scoring ─────────────────────────────────
            yield PipelineEvent(
                event_type="stage_update", stage="scoring",
                progress=0.5, message="Computing criticality scores..."
            )

            scored_findings = self.scorer.score_findings(findings)

            yield PipelineEvent(
                event_type="stage_update", stage="scoring",
                progress=0.55, message="Scoring complete",
                finding_count=len(scored_findings)
            )

            # ── Stage 4: Deduplication ───────────────────────────
            yield PipelineEvent(
                event_type="stage_update", stage="deduplicating",
                progress=0.6, message="Deduplicating findings..."
            )

            enriched = await self.report_gen.deduplicate(scored_findings)
            active = [f for f in enriched if not f.is_duplicate]

            yield PipelineEvent(
                event_type="stage_update", stage="deduplicating",
                progress=0.65, message=f"{len(active)} unique findings after dedup",
                finding_count=len(active)
            )

            # ── Stage 5: LLM Enrichment ─────────────────────────
            yield PipelineEvent(
                event_type="stage_update", stage="llm_enrichment",
                progress=0.7, message="Generating remediation guidance..."
            )

            # Generate remediation for active findings
            for i, finding in enumerate(enriched):
                if not finding.is_duplicate:
                    finding.remediation = await self.report_gen.generate_remediation(finding)

            # Coverage matrix
            coverage = self.report_gen.compute_coverage_matrix(enriched)

            # Executive summary
            exec_summary = await self.report_gen.generate_executive_summary(
                app_name=app_metadata.name,
                app_package=app_metadata.package_name,
                audit_date=app_metadata.audit_date,
                platform=app_metadata.platform,
                findings=enriched,
                coverage=coverage,
            )

            yield PipelineEvent(
                event_type="stage_update", stage="llm_enrichment",
                progress=0.85, message="LLM enrichment complete",
            )

            # ── Stage 6: Report Generation ───────────────────────
            yield PipelineEvent(
                event_type="stage_update", stage="report_generation",
                progress=0.9, message="Generating reports..."
            )

            reports_dir = Path(self.settings.reports_dir) / job_id
            reports_dir.mkdir(parents=True, exist_ok=True)

            # HTML Report
            html = self.html_gen.generate(
                findings=enriched,
                app=app_metadata,
                executive_summary=exec_summary,
                coverage=coverage,
                output_path=reports_dir / "report.html",
            )

            # PDF Report
            try:
                self.pdf_gen.generate(html, reports_dir / "report.pdf")
            except Exception as e:
                logger.warning("pdf_generation_skipped", error=str(e))

            # JSON Report
            json_data = self.json_gen.generate(
                findings=enriched,
                app=app_metadata,
                executive_summary=exec_summary,
                coverage=coverage,
                output_path=reports_dir / "policy.json",
            )

            # Store results
            results["findings"] = enriched
            results["coverage"] = coverage
            results["executive_summary"] = exec_summary
            results["json_report"] = json_data
            results["html_path"] = str(reports_dir / "report.html")
            results["pdf_path"] = str(reports_dir / "report.pdf")
            results["json_path"] = str(reports_dir / "policy.json")

            yield PipelineEvent(
                event_type="complete", stage="report_generation",
                progress=1.0,
                message=f"Audit complete! {len(active)} findings in report.",
                finding_count=len(active),
                data={"job_id": job_id},
            )

        except Exception as e:
            logger.error("pipeline_error", error=str(e))
            yield PipelineEvent(
                event_type="error", stage="error",
                progress=0.0, message=f"Pipeline error: {str(e)}"
            )

    # Store for completed pipeline results
    _results: dict[str, dict] = {}

    async def run_and_store(
        self,
        file_paths: list[str | Path],
        app_metadata: AppMetadata,
        job_id: str,
    ) -> list[PipelineEvent]:
        """Run pipeline and store results. Returns all events."""
        events = []
        async for event in self.run(file_paths, app_metadata, job_id):
            events.append(event)

        # Store the last data for retrieval
        for event in reversed(events):
            if event.event_type == "complete" and event.data:
                break

        return events
