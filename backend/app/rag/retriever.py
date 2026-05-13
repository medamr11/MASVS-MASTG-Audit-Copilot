"""
RAG retriever — semantic search over the knowledge base.
"""

from typing import Any

import chromadb

from app.models.schemas import Chunk
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class KnowledgeBaseRetriever:
    """Retrieve relevant context from the ChromaDB knowledge base."""

    COLLECTION_NAMES = [
        "masvs_controls",
        "mastg_tests",
        "maswe_weaknesses",
        "remediation_templates",
    ]

    def __init__(self, persist_dir: str | None = None):
        settings = get_settings()
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.client = chromadb.PersistentClient(path=self.persist_dir)

    def retrieve_context(
        self,
        query: str,
        filter_ids: list[str] | None = None,
        k: int = 5,
        collections: list[str] | None = None,
    ) -> list[Chunk]:
        """
        Semantic search across knowledge base collections.

        Args:
            query: Search query text
            filter_ids: Optional MASVS/MASWE IDs to filter by
            k: Number of results to return
            collections: Specific collections to search (default: all)

        Returns:
            List of Chunk objects with content and metadata
        """
        target_collections = collections or self.COLLECTION_NAMES
        all_chunks: list[Chunk] = []

        for col_name in target_collections:
            try:
                collection = self.client.get_collection(col_name)
            except Exception:
                continue

            # Build where filter if IDs provided
            where_filter = None
            if filter_ids:
                where_conditions = []
                for fid in filter_ids:
                    if fid.startswith("MASVS-"):
                        where_conditions.append({"masvs_id": {"$contains": fid}})
                    elif fid.startswith("MASWE-"):
                        where_conditions.append({"maswe_id": {"$contains": fid}})
                    elif fid.startswith("MASTG-"):
                        where_conditions.append({"mastg_test_id": {"$contains": fid}})

                if len(where_conditions) == 1:
                    where_filter = where_conditions[0]
                elif len(where_conditions) > 1:
                    where_filter = {"$or": where_conditions}

            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=min(k, 10),
                    where=where_filter,
                )
            except Exception as e:
                logger.warning("query_failed", collection=col_name, error=str(e))
                # Retry without filter
                try:
                    results = collection.query(
                        query_texts=[query],
                        n_results=min(k, 10),
                    )
                except Exception:
                    continue

            if results and results.get("documents"):
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                distances = results["distances"][0] if results.get("distances") else [1.0] * len(docs)

                for doc, meta, dist in zip(docs, metas, distances):
                    similarity = max(0.0, 1.0 - dist)  # Convert distance to similarity
                    all_chunks.append(Chunk(
                        content=doc,
                        doc_type=meta.get("doc_type", ""),
                        masvs_id=meta.get("masvs_id", ""),
                        maswe_id=meta.get("maswe_id", ""),
                        mastg_test_id=meta.get("mastg_test_id", ""),
                        section_title=meta.get("section_title", ""),
                        similarity_score=similarity,
                    ))

        # Sort by similarity and return top-k
        all_chunks.sort(key=lambda c: c.similarity_score, reverse=True)
        return all_chunks[:k]

    def retrieve_for_finding(self, finding_title: str, finding_desc: str,
                             masvs_ids: list[str] | None = None, k: int = 5) -> str:
        """
        Retrieve context for a specific finding. Returns formatted string.
        """
        query = f"{finding_title}. {finding_desc[:300]}"
        chunks = self.retrieve_context(query, filter_ids=masvs_ids, k=k)

        if not chunks:
            return "No relevant knowledge base context found."

        context_parts = []
        for chunk in chunks:
            header = chunk.section_title or chunk.doc_type
            context_parts.append(f"### {header}\n{chunk.content}")

        return "\n\n---\n\n".join(context_parts)
