"""
Finding override and knowledge search API routes.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import ScoreOverride, KnowledgeSearchRequest, KnowledgeSearchResponse
from app.rag.retriever import KnowledgeBaseRetriever
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/findings/{finding_id}/override")
async def override_score(finding_id: str, override: ScoreOverride):
    """Manually adjust score dimensions for a finding."""
    # In production, this would update the DB
    # For now, return acknowledgment
    return {
        "finding_id": finding_id,
        "updated": True,
        "override": override.model_dump(exclude_none=True),
        "message": "Score override applied. Regenerate report to reflect changes.",
    }


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(query: str, k: int = 5):
    """Search the RAG knowledge base."""
    try:
        retriever = KnowledgeBaseRetriever()
        chunks = retriever.retrieve_context(query=query, k=k)
        return KnowledgeSearchResponse(query=query, results=chunks)
    except Exception as e:
        logger.error("knowledge_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")
