"""
Report download API routes.
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/reports/{job_id}")
async def get_report_json(job_id: str):
    """Get full JSON policy report."""
    settings = get_settings()
    json_path = Path(settings.reports_dir) / job_id / "policy.json"

    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    with open(json_path) as f:
        data = json.load(f)

    return JSONResponse(content=data)


@router.get("/reports/{job_id}/html")
async def get_report_html(job_id: str):
    """Download HTML report."""
    settings = get_settings()
    html_path = Path(settings.reports_dir) / job_id / "report.html"

    if not html_path.exists():
        raise HTTPException(status_code=404, detail="HTML report not found")

    return FileResponse(
        str(html_path),
        media_type="text/html",
        filename=f"masvs_audit_report_{job_id[:8]}.html",
    )


@router.get("/reports/{job_id}/pdf")
async def get_report_pdf(job_id: str):
    """Download PDF report."""
    settings = get_settings()
    pdf_path = Path(settings.reports_dir) / job_id / "report.pdf"

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found")

    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"masvs_audit_report_{job_id[:8]}.pdf",
    )


@router.get("/reports/{job_id}/policy")
async def get_policy(job_id: str):
    """Download JSON policy output."""
    settings = get_settings()
    json_path = Path(settings.reports_dir) / job_id / "policy.json"

    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Policy report not found")

    return FileResponse(
        str(json_path),
        media_type="application/json",
        filename=f"masvs_policy_{job_id[:8]}.json",
    )
