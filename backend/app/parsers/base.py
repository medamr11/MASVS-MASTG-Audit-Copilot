"""
Abstract base class for all artifact parsers.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.models.schemas import Finding


class BaseParser(ABC):
    """Base parser interface — all parsers must implement `parse`."""

    @abstractmethod
    def parse(self, data: Any) -> list[Finding]:
        """
        Parse raw input data and return a list of canonical Findings.

        Args:
            data: Raw input data (dict, str, Path, etc. depending on parser)

        Returns:
            List of normalized Finding objects.
        """
        ...

    @staticmethod
    def _severity_normalize(raw: str) -> str:
        """Normalize severity strings to canonical values."""
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "moderate": "medium",
            "low": "low",
            "info": "info",
            "information": "info",
            "informational": "info",
            "warning": "medium",
            "secure": "info",
            "good": "info",
            "error": "high",
        }
        return mapping.get(raw.lower().strip(), "info")
