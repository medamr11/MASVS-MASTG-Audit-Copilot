"""
Pydantic v2 schemas for the MASVS Audit Copilot.
All data transfer objects and API models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingSource(str, Enum):
    MOBSF = "mobsf"
    JADX = "jadx"
    BURP = "burp"
    MANIFEST = "manifest"
    MANUAL = "manual"


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class MASVSLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"
    R = "R"


class JobStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    MAPPING = "mapping"
    SCORING = "scoring"
    DEDUPLICATING = "deduplicating"
    LLM_ENRICHMENT = "llm_enrichment"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingCategory(str, Enum):
    STORAGE = "storage"
    CRYPTO = "cryptography"
    AUTH = "authentication"
    NETWORK = "network"
    PLATFORM = "platform"
    CODE = "code"
    RESILIENCE = "resilience"
    PRIVACY = "privacy"
    OTHER = "other"


# ── Core Schemas ─────────────────────────────────────────────────────────────

class MASVSMapping(BaseModel):
    """MASVS/MASWE/MASTG mapping result for a finding."""
    maswe_ids: list[str] = Field(default_factory=list, description="MASWE weakness IDs")
    masvs_ids: list[str] = Field(default_factory=list, description="MASVS control IDs")
    mastg_tests: list[str] = Field(default_factory=list, description="MASTG test IDs")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = ""
    mapping_source: str = "rule"  # "rule" | "llm" | "manual"


class Finding(BaseModel):
    """Canonical finding schema — output from all parsers."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: FindingSource
    raw_title: str
    raw_description: str
    severity: Severity = Severity.INFO
    category: FindingCategory = FindingCategory.OTHER
    evidence: list[str] = Field(default_factory=list)
    location: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Populated by mapping engine
    masvs_mapping: MASVSMapping | None = None


class ScoredFinding(Finding):
    """Finding enriched with criticality scoring."""
    impact: int = Field(default=1, ge=1, le=5)
    exploitability: int = Field(default=1, ge=1, le=5)
    exposure: int = Field(default=1, ge=1, le=5)
    criticality_score: float = Field(default=0.0, ge=0.0, le=10.0)
    priority: Priority = Priority.P4
    masvs_level: MASVSLevel = MASVSLevel.L1
    score_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RemediationBlock(BaseModel):
    """Remediation guidance for a finding."""
    short_fix: str
    detailed_steps: list[str] = Field(default_factory=list)
    code_example: str | None = None
    references: list[str] = Field(default_factory=list)


class EnrichedFinding(ScoredFinding):
    """Fully enriched finding with remediation."""
    remediation: RemediationBlock | None = None
    duplicate_group_id: str | None = None
    is_duplicate: bool = False


# ── Job & Report Schemas ─────────────────────────────────────────────────────

class AppMetadata(BaseModel):
    """Metadata about the application being audited."""
    name: str = "Unknown App"
    package_name: str = ""
    version: str = ""
    platform: str = "android"
    audit_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    auditor: str = "MASVS Audit Copilot"


class JobCreate(BaseModel):
    """Request to create a new analysis job."""
    app_name: str = "Unknown App"
    app_package: str = ""
    app_version: str = ""


class JobResponse(BaseModel):
    """API response for job status."""
    job_id: str
    status: JobStatus
    progress: float = 0.0  # 0.0 to 1.0
    current_stage: str = ""
    finding_count: int = 0
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""


class PipelineEvent(BaseModel):
    """SSE event for pipeline progress."""
    event_type: str  # "stage_update" | "finding_added" | "error" | "complete"
    stage: str = ""
    progress: float = 0.0
    message: str = ""
    finding_count: int = 0
    data: dict[str, Any] = Field(default_factory=dict)


# ── Coverage Matrix ──────────────────────────────────────────────────────────

class CategoryCoverage(BaseModel):
    """Coverage data for a single MASVS category."""
    category: str
    total_controls: int = 0
    tested: int = 0
    passed: int = 0
    failed: int = 0
    not_tested: int = 0
    score: float = 0.0  # 0.0–10.0


class CoverageMatrix(BaseModel):
    """Full MASVS coverage matrix."""
    categories: list[CategoryCoverage] = Field(default_factory=list)
    overall_score: float = 0.0


# ── Report Schemas ───────────────────────────────────────────────────────────

class ReportMetadata(BaseModel):
    """Metadata for a generated report."""
    job_id: str
    app: AppMetadata
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    masvs_version: str = "2.1.0"
    generated_by: str = "masvs-audit-copilot"
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0


class PolicyOutput(BaseModel):
    """JSON policy output schema."""
    app: AppMetadata
    score: dict[str, Any] = Field(default_factory=dict)
    findings: list[EnrichedFinding] = Field(default_factory=list)
    coverage_matrix: CoverageMatrix = Field(default_factory=CoverageMatrix)
    executive_summary: str = ""
    generated_by: str = "masvs-audit-copilot"
    masvs_version: str = "2.1.0"


# ── Score Override ───────────────────────────────────────────────────────────

class ScoreOverride(BaseModel):
    """Manual score override request."""
    impact: int | None = Field(default=None, ge=1, le=5)
    exploitability: int | None = Field(default=None, ge=1, le=5)
    exposure: int | None = Field(default=None, ge=1, le=5)


# ── RAG Schemas ──────────────────────────────────────────────────────────────

class Chunk(BaseModel):
    """A retrieved chunk from the knowledge base."""
    content: str
    doc_type: str = ""
    masvs_id: str = ""
    maswe_id: str = ""
    mastg_test_id: str = ""
    section_title: str = ""
    similarity_score: float = 0.0


class KnowledgeSearchRequest(BaseModel):
    """RAG search request."""
    query: str
    filter_ids: list[str] | None = None
    k: int = 5


class KnowledgeSearchResponse(BaseModel):
    """RAG search response."""
    query: str
    results: list[Chunk] = Field(default_factory=list)
