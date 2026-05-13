"""
SQLAlchemy ORM models for persistent storage.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, JSON, Boolean, ForeignKey,
    create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class JobORM(Base):
    """Persistent job record."""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    status = Column(String, default="pending", nullable=False)
    progress = Column(Float, default=0.0)
    current_stage = Column(String, default="")
    app_name = Column(String, default="Unknown App")
    app_package = Column(String, default="")
    app_version = Column(String, default="")
    finding_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    findings = relationship("FindingORM", back_populates="job", cascade="all, delete-orphan")
    report = relationship("ReportORM", back_populates="job", uselist=False, cascade="all, delete-orphan")


class FindingORM(Base):
    """Persistent finding record."""
    __tablename__ = "findings"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    source = Column(String, nullable=False)
    raw_title = Column(String, nullable=False)
    raw_description = Column(Text, default="")
    severity = Column(String, default="info")
    category = Column(String, default="other")
    evidence = Column(JSON, default=list)
    location = Column(String, nullable=True)
    metadata_json = Column(JSON, default=dict)

    # MASVS mapping
    maswe_ids = Column(JSON, default=list)
    masvs_ids = Column(JSON, default=list)
    mastg_tests = Column(JSON, default=list)
    mapping_confidence = Column(Float, default=0.0)
    mapping_rationale = Column(Text, default="")
    mapping_source = Column(String, default="rule")

    # Scoring
    impact = Column(Integer, default=1)
    exploitability = Column(Integer, default=1)
    exposure = Column(Integer, default=1)
    criticality_score = Column(Float, default=0.0)
    priority = Column(String, default="P4")
    masvs_level = Column(String, default="L1")
    score_confidence = Column(Float, default=0.0)

    # Remediation
    remediation_short = Column(Text, nullable=True)
    remediation_steps = Column(JSON, default=list)
    remediation_code = Column(Text, nullable=True)
    remediation_refs = Column(JSON, default=list)

    # Deduplication
    duplicate_group_id = Column(String, nullable=True)
    is_duplicate = Column(Boolean, default=False)

    # Relationship
    job = relationship("JobORM", back_populates="findings")


class ReportORM(Base):
    """Persistent report record."""
    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, unique=True)
    executive_summary = Column(Text, default="")
    coverage_matrix = Column(JSON, default=dict)
    html_path = Column(String, nullable=True)
    pdf_path = Column(String, nullable=True)
    json_path = Column(String, nullable=True)
    report_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    job = relationship("JobORM", back_populates="report")


# ── Database session factory ─────────────────────────────────────────────────

def create_db_engine(database_url: str):
    """Create SQLAlchemy engine."""
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args, echo=False)


def create_session_factory(engine):
    """Create session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine):
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
