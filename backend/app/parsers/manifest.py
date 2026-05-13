"""
AndroidManifest.xml parser.
Extracts security-relevant configurations and exported components.
"""

from typing import Any

from defusedxml import ElementTree as ET

from app.models.schemas import Finding, FindingSource, Severity, FindingCategory
from app.parsers.base import BaseParser

ANDROID_NS = "http://schemas.android.com/apk/res/android"


class ManifestParser(BaseParser):
    """Parse AndroidManifest.xml for security issues."""

    def parse(self, data: Any) -> list[Finding]:
        """Parse AndroidManifest.xml. `data` is file path or XML string."""
        findings: list[Finding] = []

        try:
            if isinstance(data, str) and not data.strip().startswith("<"):
                tree = ET.parse(data)
                root = tree.getroot()
            else:
                root = ET.fromstring(data if isinstance(data, str) else data.encode())
        except Exception as e:
            return [Finding(
                source=FindingSource.MANIFEST,
                raw_title="Manifest Parse Error",
                raw_description=f"Failed to parse AndroidManifest.xml: {str(e)}",
                severity=Severity.INFO,
                category=FindingCategory.OTHER,
            )]

        findings.extend(self._check_app_flags(root))
        findings.extend(self._check_exported_components(root))
        findings.extend(self._check_permissions(root))
        findings.extend(self._check_sdk_versions(root))

        return findings

    def _attr(self, el, name: str) -> str | None:
        """Get android: namespaced attribute."""
        return el.get(f"{{{ANDROID_NS}}}{name}")

    def _check_app_flags(self, root) -> list[Finding]:
        """Check application-level security flags."""
        findings = []
        app = root.find("application")
        if app is None:
            return findings

        # Debuggable
        if self._attr(app, "debuggable") == "true":
            findings.append(Finding(
                source=FindingSource.MANIFEST,
                raw_title="Application is Debuggable",
                raw_description="android:debuggable is set to true. This allows attackers to attach a debugger, inspect memory, and bypass security controls.",
                severity=Severity.HIGH,
                category=FindingCategory.RESILIENCE,
                evidence=["android:debuggable=\"true\""],
                location="AndroidManifest.xml",
                metadata={"flag": "debuggable"},
            ))

        # AllowBackup
        if self._attr(app, "allowBackup") != "false":
            findings.append(Finding(
                source=FindingSource.MANIFEST,
                raw_title="Application Allows Backup",
                raw_description="android:allowBackup is not explicitly set to false. App data can be extracted via ADB backup.",
                severity=Severity.MEDIUM,
                category=FindingCategory.STORAGE,
                evidence=["android:allowBackup is not false"],
                location="AndroidManifest.xml",
                metadata={"flag": "allowBackup"},
            ))

        # Cleartext traffic
        if self._attr(app, "usesCleartextTraffic") == "true":
            findings.append(Finding(
                source=FindingSource.MANIFEST,
                raw_title="Cleartext Traffic Permitted",
                raw_description="android:usesCleartextTraffic is true. Unencrypted HTTP traffic is allowed.",
                severity=Severity.HIGH,
                category=FindingCategory.NETWORK,
                evidence=["android:usesCleartextTraffic=\"true\""],
                location="AndroidManifest.xml",
                metadata={"flag": "usesCleartextTraffic"},
            ))

        # Network security config
        nsc = self._attr(app, "networkSecurityConfig")
        if not nsc:
            findings.append(Finding(
                source=FindingSource.MANIFEST,
                raw_title="No Network Security Config",
                raw_description="No custom network security configuration defined. Consider adding one to enforce certificate pinning and restrict cleartext traffic.",
                severity=Severity.LOW,
                category=FindingCategory.NETWORK,
                evidence=[],
                location="AndroidManifest.xml",
                metadata={"flag": "networkSecurityConfig"},
            ))

        return findings

    def _check_exported_components(self, root) -> list[Finding]:
        """Check for exported components without permissions."""
        findings = []
        app = root.find("application")
        if app is None:
            return findings

        component_types = ["activity", "service", "receiver", "provider"]

        for comp_type in component_types:
            for comp in app.findall(comp_type):
                name = self._attr(comp, "name") or "unknown"
                exported = self._attr(comp, "exported")
                permission = self._attr(comp, "permission")

                # Check intent filters (implicit export)
                has_intent_filter = comp.find("intent-filter") is not None
                is_exported = exported == "true" or (exported is None and has_intent_filter)

                if is_exported and not permission:
                    severity = Severity.HIGH if comp_type in ("provider", "service") else Severity.MEDIUM
                    findings.append(Finding(
                        source=FindingSource.MANIFEST,
                        raw_title=f"Exported {comp_type.title()} Without Permission: {name}",
                        raw_description=f"The {comp_type} '{name}' is exported without requiring a permission. Any app on the device can interact with it.",
                        severity=severity,
                        category=FindingCategory.PLATFORM,
                        evidence=[f"<{comp_type} android:name=\"{name}\" android:exported=\"true\">"],
                        location="AndroidManifest.xml",
                        metadata={"component_type": comp_type, "component_name": name, "exported": True},
                    ))

        return findings

    def _check_permissions(self, root) -> list[Finding]:
        """Check for custom permissions with weak protection levels."""
        findings = []

        for perm in root.findall("permission"):
            name = self._attr(perm, "name") or "unknown"
            protection = self._attr(perm, "protectionLevel") or "normal"

            if protection.lower() in ("normal", "dangerous"):
                findings.append(Finding(
                    source=FindingSource.MANIFEST,
                    raw_title=f"Weak Custom Permission: {name}",
                    raw_description=f"Custom permission '{name}' uses protection level '{protection}'. Consider using 'signature' to restrict to same-signing-key apps.",
                    severity=Severity.LOW,
                    category=FindingCategory.PLATFORM,
                    evidence=[f"protectionLevel=\"{protection}\""],
                    location="AndroidManifest.xml",
                    metadata={"permission": name, "protectionLevel": protection},
                ))

        return findings

    def _check_sdk_versions(self, root) -> list[Finding]:
        """Check min/target SDK versions."""
        findings = []
        uses_sdk = root.find("uses-sdk")
        if uses_sdk is None:
            return findings

        min_sdk = self._attr(uses_sdk, "minSdkVersion")
        target_sdk = self._attr(uses_sdk, "targetSdkVersion")

        if min_sdk and int(min_sdk) < 23:
            findings.append(Finding(
                source=FindingSource.MANIFEST,
                raw_title=f"Low minSdkVersion: {min_sdk}",
                raw_description=f"minSdkVersion is {min_sdk} (< 23). Android versions before 6.0 lack runtime permissions and other security features.",
                severity=Severity.MEDIUM,
                category=FindingCategory.PLATFORM,
                evidence=[f"minSdkVersion=\"{min_sdk}\""],
                location="AndroidManifest.xml",
                metadata={"minSdkVersion": min_sdk},
            ))

        if target_sdk and int(target_sdk) < 31:
            findings.append(Finding(
                source=FindingSource.MANIFEST,
                raw_title=f"Low targetSdkVersion: {target_sdk}",
                raw_description=f"targetSdkVersion is {target_sdk} (< 31). Targeting older SDK versions disables newer security defaults.",
                severity=Severity.LOW,
                category=FindingCategory.PLATFORM,
                evidence=[f"targetSdkVersion=\"{target_sdk}\""],
                location="AndroidManifest.xml",
                metadata={"targetSdkVersion": target_sdk},
            ))

        return findings
