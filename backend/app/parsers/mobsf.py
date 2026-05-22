"""
MobSF JSON export parser.
Extracts findings from MobSF static analysis JSON reports.
"""

from typing import Any

from app.models.schemas import Finding, FindingSource, Severity, FindingCategory
from app.parsers.base import BaseParser


class MobSFParser(BaseParser):
    """Parse MobSF JSON export into canonical Finding objects."""

    # Map MobSF sections to finding categories
    SECTION_CATEGORY_MAP = {
        "code_analysis": FindingCategory.CODE,
        "manifest_analysis": FindingCategory.PLATFORM,
        "network_security": FindingCategory.NETWORK,
        "certificate_analysis": FindingCategory.CRYPTO,
        "binary_analysis": FindingCategory.RESILIENCE,
        "file_analysis": FindingCategory.STORAGE,
    }

    def parse(self, data: dict[str, Any]) -> list[Finding]:
        """Parse a MobSF JSON report dict."""
        findings: list[Finding] = []

        # Extract app metadata for context
        app_name = data.get("app_name", "Unknown")
        package = data.get("package_name", "")

        # ── Code Analysis (SAST) ─────────────────────────────────
        findings.extend(self._parse_code_analysis(data))

        # ── Manifest Analysis ────────────────────────────────────
        findings.extend(self._parse_manifest_analysis(data))

        # ── Network Security ─────────────────────────────────────
        findings.extend(self._parse_network_security(data))

        # ── Certificate Analysis ─────────────────────────────────
        findings.extend(self._parse_certificate_analysis(data))

        # ── Permissions ──────────────────────────────────────────
        findings.extend(self._parse_permissions(data))

        # ── Binary Analysis ──────────────────────────────────────
        findings.extend(self._parse_binary_analysis(data))

        # ── File Analysis ────────────────────────────────────────
        findings.extend(self._parse_file_analysis(data))

        return findings

    def _parse_code_analysis(self, data: dict) -> list[Finding]:
        """Parse code_analysis section."""
        findings = []
        code_analysis = data.get("code_analysis", {})
        
        # Handle newer MobSF format where findings are under 'findings' key
        findings_data = code_analysis.get("findings", code_analysis)
        if not isinstance(findings_data, dict):
            findings_data = {}

        for rule_id, details in findings_data.items():
            if not isinstance(details, dict):
                continue

            severity_raw = details.get("metadata", {}).get("severity", "info") \
                if isinstance(details.get("metadata"), dict) \
                else details.get("severity", "info")

            # Handle both old and new MobSF formats
            description = details.get("metadata", {}).get("description", "") \
                if isinstance(details.get("metadata"), dict) \
                else details.get("description", "")

            # Collect evidence from file paths
            evidence = []
            files = details.get("files", {})
            if isinstance(files, dict):
                for filepath, line_info in list(files.items())[:5]:
                    evidence.append(f"{filepath}: {line_info}")
            elif isinstance(files, list):
                evidence = [str(f) for f in files[:5]]

            severity_str = self._severity_normalize(str(severity_raw))

            findings.append(Finding(
                source=FindingSource.MOBSF,
                raw_title=rule_id,
                raw_description=str(description),
                severity=Severity(severity_str),
                category=FindingCategory.CODE,
                evidence=evidence,
                location=None,
                metadata={"section": "code_analysis", "rule_id": rule_id},
            ))

        return findings

    def _parse_manifest_analysis(self, data: dict) -> list[Finding]:
        """Parse manifest_analysis section."""
        findings = []
        manifest = data.get("manifest_analysis", [])

        # Handle newer MobSF format where findings are under 'manifest_findings' key
        if isinstance(manifest, dict):
            manifest = manifest.get("manifest_findings", [])

        if isinstance(manifest, list):
            for item in manifest:
                if not isinstance(item, dict):
                    continue

                severity_raw = item.get("severity", item.get("stat", "info"))
                severity_str = self._severity_normalize(str(severity_raw))

                title = item.get("title", item.get("rule", "Manifest Issue"))
                desc = item.get("description", item.get("desc", ""))

                findings.append(Finding(
                    source=FindingSource.MOBSF,
                    raw_title=str(title),
                    raw_description=str(desc),
                    severity=Severity(severity_str),
                    category=FindingCategory.PLATFORM,
                    evidence=[str(item.get("component", ""))],
                    location="AndroidManifest.xml",
                    metadata={"section": "manifest_analysis"},
                ))

        return findings

    def _parse_network_security(self, data: dict) -> list[Finding]:
        """Parse network_security section."""
        findings = []
        network = data.get("network_security", data.get("network_findings", []))

        if isinstance(network, list):
            for item in network:
                if not isinstance(item, dict):
                    continue

                severity_str = self._severity_normalize(
                    str(item.get("severity", "medium"))
                )

                findings.append(Finding(
                    source=FindingSource.MOBSF,
                    raw_title=str(item.get("title", item.get("scope", "Network Issue"))),
                    raw_description=str(item.get("description", "")),
                    severity=Severity(severity_str),
                    category=FindingCategory.NETWORK,
                    evidence=[str(item.get("description", ""))],
                    metadata={"section": "network_security"},
                ))
        elif isinstance(network, dict):
            # Handle dict format
            for key, value in network.items():
                if isinstance(value, dict):
                    severity_str = self._severity_normalize(
                        str(value.get("severity", "medium"))
                    )
                    findings.append(Finding(
                        source=FindingSource.MOBSF,
                        raw_title=str(value.get("title", key)),
                        raw_description=str(value.get("description", "")),
                        severity=Severity(severity_str),
                        category=FindingCategory.NETWORK,
                        evidence=[],
                        metadata={"section": "network_security"},
                    ))

        return findings

    def _parse_certificate_analysis(self, data: dict) -> list[Finding]:
        """Parse certificate_analysis section."""
        findings = []
        cert = data.get("certificate_analysis", data.get("certificate_info", {}))

        if isinstance(cert, dict):
            cert_findings = cert.get("certificate_findings", [])
            if isinstance(cert_findings, list):
                for item in cert_findings:
                    # Handle both list format [severity, desc, title] and dict format
                    if isinstance(item, list) and len(item) >= 3:
                        severity_raw = item[0]
                        desc = item[1]
                        title = item[2]
                    elif isinstance(item, dict):
                        severity_raw = item.get("severity", "info")
                        title = item.get("title", "Certificate Issue")
                        desc = item.get("description", "")
                    else:
                        continue
                        
                    severity_str = self._severity_normalize(str(severity_raw))
                    findings.append(Finding(
                        source=FindingSource.MOBSF,
                        raw_title=str(title),
                        raw_description=str(desc),
                        severity=Severity(severity_str),
                        category=FindingCategory.CRYPTO,
                        evidence=[],
                        metadata={"section": "certificate_analysis"},
                    ))

        return findings

    def _parse_permissions(self, data: dict) -> list[Finding]:
        """Parse permissions section — flag dangerous permissions."""
        findings = []
        permissions = data.get("permissions", {})

        DANGEROUS_PERMS = {
            "android.permission.READ_CONTACTS",
            "android.permission.WRITE_CONTACTS",
            "android.permission.READ_CALL_LOG",
            "android.permission.CAMERA",
            "android.permission.RECORD_AUDIO",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.ACCESS_COARSE_LOCATION",
            "android.permission.READ_PHONE_STATE",
            "android.permission.SEND_SMS",
            "android.permission.READ_SMS",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.WRITE_EXTERNAL_STORAGE",
            "android.permission.READ_CALENDAR",
        }

        if isinstance(permissions, dict):
            for perm_name, perm_info in permissions.items():
                if perm_name in DANGEROUS_PERMS:
                    status = "dangerous"
                    desc = perm_info if isinstance(perm_info, str) else \
                        perm_info.get("description", "") if isinstance(perm_info, dict) else ""

                    findings.append(Finding(
                        source=FindingSource.MOBSF,
                        raw_title=f"Dangerous Permission: {perm_name}",
                        raw_description=f"Application requests dangerous permission: {perm_name}. {desc}",
                        severity=Severity.MEDIUM,
                        category=FindingCategory.PRIVACY,
                        evidence=[perm_name],
                        location="AndroidManifest.xml",
                        metadata={"section": "permissions", "permission": perm_name, "status": status},
                    ))

        return findings

    def _parse_binary_analysis(self, data: dict) -> list[Finding]:
        """Parse binary_analysis section."""
        findings = []
        binary = data.get("binary_analysis", [])

        if isinstance(binary, list):
            for item in binary:
                if not isinstance(item, dict):
                    continue
                severity_str = self._severity_normalize(
                    str(item.get("severity", "info"))
                )
                findings.append(Finding(
                    source=FindingSource.MOBSF,
                    raw_title=str(item.get("title", item.get("name", "Binary Issue"))),
                    raw_description=str(item.get("description", item.get("desc", ""))),
                    severity=Severity(severity_str),
                    category=FindingCategory.RESILIENCE,
                    evidence=[],
                    metadata={"section": "binary_analysis"},
                ))

        return findings

    def _parse_file_analysis(self, data: dict) -> list[Finding]:
        """Parse file_analysis section for sensitive data exposure."""
        findings = []
        file_analysis = data.get("file_analysis", data.get("urls", []))

        # Check for hardcoded URLs / IPs
        urls = data.get("urls", [])
        if isinstance(urls, list) and urls:
            for url_item in urls[:10]:
                url_str = str(url_item.get("urls", url_item) if isinstance(url_item, dict) else url_item)
                if "http://" in url_str.lower():
                    findings.append(Finding(
                        source=FindingSource.MOBSF,
                        raw_title="Hardcoded HTTP URL",
                        raw_description=f"Application contains hardcoded HTTP (non-HTTPS) URL: {url_str[:200]}",
                        severity=Severity.MEDIUM,
                        category=FindingCategory.NETWORK,
                        evidence=[url_str[:500]],
                        metadata={"section": "urls"},
                    ))

        return findings
