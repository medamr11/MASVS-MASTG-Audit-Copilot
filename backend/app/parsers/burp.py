"""
Burp Suite XML export parser.
Parses Burp issue export XML files into canonical Findings.
"""

import base64
from typing import Any

from defusedxml import ElementTree as ET

from app.models.schemas import Finding, FindingSource, Severity, FindingCategory
from app.parsers.base import BaseParser


class BurpParser(BaseParser):
    """Parse Burp Suite XML export into canonical Finding objects."""

    SEVERITY_MAP = {
        "high": "high",
        "medium": "medium",
        "low": "low",
        "information": "info",
        "info": "info",
        "false positive": "info",
    }

    CATEGORY_MAP = {
        "sql injection": FindingCategory.CODE,
        "cross-site scripting": FindingCategory.CODE,
        "xss": FindingCategory.CODE,
        "tls": FindingCategory.NETWORK,
        "ssl": FindingCategory.NETWORK,
        "certificate": FindingCategory.CRYPTO,
        "authentication": FindingCategory.AUTH,
        "authorization": FindingCategory.AUTH,
        "session": FindingCategory.AUTH,
        "cookie": FindingCategory.AUTH,
        "cleartext": FindingCategory.NETWORK,
        "encryption": FindingCategory.CRYPTO,
        "information disclosure": FindingCategory.STORAGE,
        "open redirect": FindingCategory.CODE,
        "csrf": FindingCategory.CODE,
        "cors": FindingCategory.NETWORK,
    }

    def parse(self, data: Any) -> list[Finding]:
        """Parse Burp XML export. `data` can be a file path string or XML string."""
        findings: list[Finding] = []

        try:
            if isinstance(data, str) and not data.strip().startswith("<"):
                tree = ET.parse(data)
                root = tree.getroot()
            else:
                root = ET.fromstring(data if isinstance(data, str) else data.encode())
        except Exception as e:
            return [Finding(
                source=FindingSource.BURP,
                raw_title="Burp XML Parse Error",
                raw_description=f"Failed to parse Burp XML: {str(e)}",
                severity=Severity.INFO,
                category=FindingCategory.OTHER,
            )]

        issues = root.findall(".//issue") if root.tag != "issue" else [root]
        if not issues and root.tag == "issues":
            issues = list(root)

        for issue in issues:
            findings.append(self._parse_issue(issue))

        return findings

    def _parse_issue(self, issue_el) -> Finding:
        """Parse a single <issue> element."""
        name = self._get_text(issue_el, "name", "Unknown Burp Issue")
        severity_raw = self._get_text(issue_el, "severity", "info")
        host = self._get_text(issue_el, "host", "")
        path = self._get_text(issue_el, "path", "")
        location = self._get_text(issue_el, "location", "")
        confidence = self._get_text(issue_el, "confidence", "")

        # Build description from available fields
        background = self._get_text(issue_el, "issueBackground", "")
        detail = self._get_text(issue_el, "issueDetail", "")
        remediation_bg = self._get_text(issue_el, "remediationBackground", "")
        remediation_detail = self._get_text(issue_el, "remediationDetail", "")
        desc = f"{detail}\n\n{background}".strip() or name

        # Extract request/response evidence
        evidence = []
        for rr in issue_el.findall(".//requestresponse"):
            req_el = rr.find("request")
            resp_el = rr.find("response")
            if req_el is not None and req_el.text:
                req_text = self._decode_content(req_el)
                evidence.append(f"REQUEST:\n{req_text[:800]}")
            if resp_el is not None and resp_el.text:
                resp_text = self._decode_content(resp_el)
                evidence.append(f"RESPONSE:\n{resp_text[:800]}")

        # Determine category from name
        category = FindingCategory.OTHER
        name_lower = name.lower()
        for keyword, cat in self.CATEGORY_MAP.items():
            if keyword in name_lower:
                category = cat
                break

        severity_str = self.SEVERITY_MAP.get(severity_raw.lower().strip(), "info")
        endpoint = f"{host}{path}" if host else location

        return Finding(
            source=FindingSource.BURP,
            raw_title=name,
            raw_description=desc,
            severity=Severity(severity_str),
            category=category,
            evidence=evidence[:4],
            location=endpoint or None,
            metadata={
                "confidence": confidence,
                "remediation": f"{remediation_detail}\n{remediation_bg}".strip(),
                "host": host,
                "path": path,
                "burp_type": self._get_text(issue_el, "type", ""),
            },
        )

    @staticmethod
    def _get_text(el, tag: str, default: str = "") -> str:
        child = el.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return default

    @staticmethod
    def _decode_content(el) -> str:
        """Decode base64-encoded or plain text content."""
        text = el.text or ""
        is_base64 = el.get("base64", "false").lower() == "true"
        if is_base64:
            try:
                return base64.b64decode(text).decode("utf-8", errors="replace")
            except Exception:
                return text
        return text
