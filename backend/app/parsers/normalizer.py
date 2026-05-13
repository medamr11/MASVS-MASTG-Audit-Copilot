"""
Finding normalizer — unified entry point for all parsers.
Auto-detects file type and dispatches to the correct parser.
"""

import json
from pathlib import Path
from typing import Any

from app.models.schemas import Finding
from app.parsers.base import BaseParser
from app.parsers.mobsf import MobSFParser
from app.parsers.jadx import JADXParser
from app.parsers.burp import BurpParser
from app.parsers.manifest import ManifestParser
from app.core.logging import get_logger

logger = get_logger(__name__)


class FindingNormalizer:
    """
    Unified entry point that auto-detects artifact types and
    dispatches to the appropriate parser.
    """

    def __init__(self):
        self.mobsf = MobSFParser()
        self.jadx = JADXParser()
        self.burp = BurpParser()
        self.manifest = ManifestParser()

    def normalize(self, file_path: str | Path, content: bytes | None = None) -> list[Finding]:
        """
        Parse a file and return normalized findings.

        Args:
            file_path: Path to the artifact file
            content: Optional pre-read content bytes

        Returns:
            List of canonical Finding objects
        """
        path = Path(file_path)
        filename = path.name.lower()

        if content is None:
            content = path.read_bytes()

        text = content.decode("utf-8", errors="replace")

        file_type = self.detect_type(filename, text)
        logger.info("detected_file_type", file=filename, type=file_type)

        if file_type == "mobsf":
            data = json.loads(text)
            return self.mobsf.parse(data)
        elif file_type == "burp":
            return self.burp.parse(text)
        elif file_type == "manifest":
            return self.manifest.parse(text)
        elif file_type == "jadx":
            return self.jadx.parse([{"path": str(path), "content": text}])
        else:
            logger.warning("unknown_file_type", file=filename)
            return []

    def normalize_directory(self, dir_path: str | Path) -> list[Finding]:
        """Parse all files in a directory."""
        findings: list[Finding] = []
        dir_path = Path(dir_path)

        for file_path in dir_path.iterdir():
            if file_path.is_file():
                try:
                    findings.extend(self.normalize(file_path))
                except Exception as e:
                    logger.error("parse_error", file=str(file_path), error=str(e))

        return findings

    def normalize_multiple(self, file_paths: list[str | Path]) -> list[Finding]:
        """Parse multiple files and return combined findings."""
        findings: list[Finding] = []

        for fp in file_paths:
            path = Path(fp)
            if path.is_dir():
                # JADX directory
                findings.extend(self.jadx.parse(path))
            elif path.is_file():
                try:
                    findings.extend(self.normalize(path))
                except Exception as e:
                    logger.error("parse_error", file=str(path), error=str(e))

        logger.info("normalization_complete", total_findings=len(findings))
        return findings

    @staticmethod
    def detect_type(filename: str, content: str) -> str:
        """Detect artifact type from filename and content."""
        filename = filename.lower()

        # AndroidManifest.xml
        if "manifest" in filename and filename.endswith(".xml"):
            return "manifest"

        # Burp XML
        if filename.endswith(".xml"):
            if "<issues" in content[:500] or "<issue>" in content[:500]:
                return "burp"

        # MobSF JSON
        if filename.endswith(".json"):
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    mobsf_keys = {"app_name", "package_name", "code_analysis",
                                  "manifest_analysis", "certificate_analysis",
                                  "network_security", "permissions"}
                    if len(mobsf_keys & set(data.keys())) >= 2:
                        return "mobsf"
            except json.JSONDecodeError:
                pass

        # Java source
        if filename.endswith(".java"):
            return "jadx"

        # Generic XML check
        if content.strip().startswith("<?xml") or content.strip().startswith("<"):
            if "<manifest" in content[:1000]:
                return "manifest"
            if "<issues" in content[:500]:
                return "burp"

        return "unknown"
