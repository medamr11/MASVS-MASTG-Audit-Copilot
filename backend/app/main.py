"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.api.reports import router as reports_router
from app.api.findings import router as findings_router
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.models.orm import create_db_engine, create_session_factory, init_db
from app.rag.indexer import KnowledgeBaseIndexer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings = get_settings()
    setup_logging()
    logger = get_logger("startup")

    # Initialize database
    engine = create_db_engine(settings.database_url)
    init_db(engine)
    app.state.db_session_factory = create_session_factory(engine)
    logger.info("database_initialized", url=settings.database_url)

    # Create directories
    Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)

    # Index knowledge base (only if not already indexed)
    try:
        indexer = KnowledgeBaseIndexer()
        counts = indexer.index_all()
        logger.info("knowledge_base_indexed", counts=counts)
    except Exception as e:
        logger.warning("knowledge_base_index_failed", error=str(e))

    yield

    # Cleanup
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="MASVS Audit Copilot",
        description="Transform mobile security analysis artifacts into structured MASVS v2 audit reports",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
    app.include_router(reports_router, prefix="/api", tags=["Reports"])
    app.include_router(findings_router, prefix="/api", tags=["Findings & Knowledge"])

    @app.get("/api/health")
    async def health():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "llm_configured": bool(settings.gemini_api_key),
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
