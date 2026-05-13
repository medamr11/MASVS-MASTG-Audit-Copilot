"""
Knowledge base indexer.
Chunks documents and indexes them into ChromaDB collections.
"""

import json
import re
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class KnowledgeBaseIndexer:
    """Index MASVS/MASTG/MASWE documents into ChromaDB."""

    def __init__(self, persist_dir: str | None = None):
        settings = get_settings()
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.kb_dir = Path(settings.knowledge_base_dir)
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        logger.info("chroma_client_initialized", persist_dir=self.persist_dir)

    def index_all(self) -> dict[str, int]:
        """Index all knowledge base documents. Returns count per collection."""
        counts = {}

        counts["masvs_controls"] = self._index_markdown(
            collection_name="masvs_controls",
            file_path=self.kb_dir / "masvs" / "controls.md",
            doc_type="masvs",
            id_pattern=r"MASVS-\w+-\d+",
        )

        counts["mastg_tests"] = self._index_markdown(
            collection_name="mastg_tests",
            file_path=self.kb_dir / "mastg" / "test_cases.md",
            doc_type="mastg",
            id_pattern=r"MASTG-TEST-\d+",
        )

        counts["maswe_weaknesses"] = self._index_markdown(
            collection_name="maswe_weaknesses",
            file_path=self.kb_dir / "maswe" / "weaknesses.md",
            doc_type="maswe",
            id_pattern=r"MASWE-\d+",
        )

        counts["remediation_templates"] = self._index_remediation_templates()

        logger.info("indexing_complete", counts=counts)
        return counts

    def _index_markdown(
        self,
        collection_name: str,
        file_path: Path,
        doc_type: str,
        id_pattern: str,
    ) -> int:
        """Chunk and index a markdown file."""
        if not file_path.exists():
            logger.warning("file_not_found", path=str(file_path))
            return 0

        content = file_path.read_text()
        chunks = self._chunk_by_section(content, id_pattern)

        if not chunks:
            return 0

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Clear existing documents
        try:
            existing = collection.get()
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_type}_{i}"
            ids.append(chunk_id)
            documents.append(chunk["content"])

            # Extract IDs from content
            masvs_ids = re.findall(r"MASVS-\w+-\d+", chunk["content"])
            maswe_ids = re.findall(r"MASWE-\d+", chunk["content"])
            mastg_ids = re.findall(r"MASTG-TEST-\d+", chunk["content"])

            metadatas.append({
                "doc_type": doc_type,
                "section_title": chunk.get("title", ""),
                "masvs_id": ",".join(set(masvs_ids)) if masvs_ids else "",
                "maswe_id": ",".join(set(maswe_ids)) if maswe_ids else "",
                "mastg_test_id": ",".join(set(mastg_ids)) if mastg_ids else "",
            })

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("collection_indexed", name=collection_name, chunks=len(ids))
        return len(ids)

    def _index_remediation_templates(self) -> int:
        """Index remediation templates from JSON."""
        file_path = self.kb_dir / "remediation_templates.json"
        if not file_path.exists():
            return 0

        with open(file_path) as f:
            data = json.load(f)

        templates = data.get("templates", [])
        if not templates:
            return 0

        collection = self.client.get_or_create_collection(
            name="remediation_templates",
            metadata={"hnsw:space": "cosine"},
        )

        try:
            existing = collection.get()
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

        ids = []
        documents = []
        metadatas = []

        for i, tmpl in enumerate(templates):
            doc = f"## {tmpl['title']}\n\n"
            doc += f"**Fix:** {tmpl['short_fix']}\n\n"
            doc += "**Steps:**\n" + "\n".join(f"- {s}" for s in tmpl.get("steps", []))
            if tmpl.get("code_example"):
                doc += f"\n\n**Code:**\n```\n{tmpl['code_example']}\n```"
            if tmpl.get("references"):
                doc += f"\n\n**References:** {', '.join(tmpl['references'])}"

            ids.append(f"remediation_{i}")
            documents.append(doc)
            metadatas.append({
                "doc_type": "remediation",
                "masvs_id": tmpl.get("masvs_id", ""),
                "section_title": tmpl.get("title", ""),
                "maswe_id": "",
                "mastg_test_id": "",
            })

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("remediation_indexed", count=len(ids))
        return len(ids)

    def _chunk_by_section(self, content: str, id_pattern: str) -> list[dict]:
        """Split markdown into sections based on ## headers."""
        sections = re.split(r'\n(?=## )', content)
        chunks = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extract title from first line
            lines = section.split("\n", 1)
            title = lines[0].replace("## ", "").replace("# ", "").strip()

            # If section is too long, sub-chunk
            if len(section) > self.chunk_size * 4:
                sub_chunks = self._chunk_text(section, self.chunk_size, self.chunk_overlap)
                for sc in sub_chunks:
                    chunks.append({"title": title, "content": sc})
            else:
                chunks.append({"title": title, "content": section})

        return chunks

    @staticmethod
    def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
        """Simple character-based chunking with overlap."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start = end - overlap
        return chunks
