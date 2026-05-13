"""
Analysis and Job API routes.
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import JobResponse, JobStatus, AppMetadata, PipelineEvent
from app.pipeline import AnalysisPipeline
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In-memory job storage (replace with DB in production)
jobs: dict[str, dict[str, Any]] = {}
job_events: dict[str, list[PipelineEvent]] = {}
job_results: dict[str, dict] = {}


@router.post("/analyze", response_model=JobResponse)
async def analyze(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    app_name: str = Form(default="Unknown App"),
    app_package: str = Form(default=""),
    app_version: str = Form(default=""),
):
    """Upload files and start the analysis pipeline."""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_FILES = 10
    ALLOWED_EXTENSIONS = {".json", ".xml", ".java", ".kt", ".txt"}

    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_FILES} files allowed per analysis.")

    job_id = str(uuid.uuid4())
    settings = get_settings()

    # Save uploaded files with validation
    upload_dir = Path(settings.uploads_dir) / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_paths = []
    for f in files:
        # Validate file size
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File '{f.filename}' exceeds 50MB limit.")

        # Sanitize filename (prevent path traversal)
        safe_name = Path(f.filename).name.replace("..", "").replace("/", "_").replace("\\", "_")
        if not safe_name:
            safe_name = f"upload_{uuid.uuid4().hex[:8]}"

        # Validate extension
        ext = Path(safe_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning("unsupported_file_type", filename=safe_name, extension=ext)

        file_path = upload_dir / safe_name
        file_path.write_bytes(content)
        file_paths.append(str(file_path))

    # Create job
    app_metadata = AppMetadata(
        name=app_name,
        package_name=app_package,
        version=app_version,
    )

    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "progress": 0.0,
        "current_stage": "",
        "finding_count": 0,
        "error": None,
        "created_at": app_metadata.audit_date,
        "updated_at": app_metadata.audit_date,
        "app_metadata": app_metadata,
    }
    job_events[job_id] = []

    # Start pipeline in background
    background_tasks.add_task(run_pipeline, job_id, file_paths, app_metadata)

    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=app_metadata.audit_date,
        updated_at=app_metadata.audit_date,
    )


async def run_pipeline(job_id: str, file_paths: list[str], app_metadata: AppMetadata):
    """Background task to run the analysis pipeline."""
    pipeline = AnalysisPipeline()

    try:
        async for event in pipeline.run(file_paths, app_metadata, job_id):
            # Update job state
            if job_id in jobs:
                jobs[job_id]["progress"] = event.progress
                jobs[job_id]["current_stage"] = event.stage
                jobs[job_id]["finding_count"] = event.finding_count or jobs[job_id]["finding_count"]

                if event.event_type == "stage_update":
                    jobs[job_id]["status"] = JobStatus(event.stage) if event.stage in [e.value for e in JobStatus] else jobs[job_id]["status"]
                elif event.event_type == "complete":
                    jobs[job_id]["status"] = JobStatus.COMPLETED
                    if event.data:
                        job_results[job_id] = event.data
                elif event.event_type == "error":
                    jobs[job_id]["status"] = JobStatus.FAILED
                    jobs[job_id]["error"] = event.message

            # Store event for SSE
            if job_id in job_events:
                job_events[job_id].append(event)

    except Exception as e:
        logger.error("pipeline_background_error", job_id=job_id, error=str(e))
        if job_id in jobs:
            jobs[job_id]["status"] = JobStatus.FAILED
            jobs[job_id]["error"] = str(e)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        current_stage=job["current_stage"],
        finding_count=job["finding_count"],
        error=job.get("error"),
        created_at=job.get("created_at", ""),
        updated_at=job.get("updated_at", ""),
    )


@router.get("/jobs/{job_id}/events")
async def job_events_sse(job_id: str):
    """SSE stream of pipeline progress events."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_idx = 0
        while True:
            if job_id in job_events:
                events = job_events[job_id]
                while last_idx < len(events):
                    event = events[last_idx]
                    last_idx += 1
                    yield {
                        "event": event.event_type,
                        "data": event.model_dump_json(),
                    }
                    if event.event_type in ("complete", "error"):
                        return

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
