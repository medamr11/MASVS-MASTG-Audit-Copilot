"""
JADX decompiled source code parser.
Scans .java files for security anti-patterns using regex-based rules.
"""

import re
from pathlib import Path
from typing import Any

from app.models.schemas import Finding, FindingSource, Severity, FindingCategory
from app.parsers.base import BaseParser


# Rule tuple: (rule_id, title, pattern, severity, category, description)
_RULES = [
    ("JADX-SECRET-001", "Hardcoded API Key",
     re.compile(r'''(?:api[_-]?key|apikey)\s*[=:]\s*["']([a-zA-Z0-9_\-]{16,})["']''', re.I),
     "high", FindingCategory.CRYPTO,
     "Hardcoded API key found. Store secrets in Android Keystore or inject at build time."),
    ("JADX-SECRET-002", "Hardcoded Password",
     re.compile(r'''(?:password|passwd|pwd|secret)\s*[=:]\s*["']([^"']{4,})["']''', re.I),
     "critical", FindingCategory.CRYPTO,
     "Hardcoded password found. Credentials must never be embedded in code."),
    ("JADX-SECRET-003", "Hardcoded Token",
     re.compile(r'''(?:token|bearer|auth)\s*[=:]\s*["']([a-zA-Z0-9_\-.]{20,})["']''', re.I),
     "high", FindingCategory.AUTH,
     "Hardcoded auth token found. Obtain tokens dynamically and store securely."),
    ("JADX-SECRET-004", "AWS Access Key",
     re.compile(r'AKIA[0-9A-Z]{16}'),
     "critical", FindingCategory.CRYPTO,
     "AWS Access Key ID in source. Cloud credentials must never be in mobile apps."),
    ("JADX-CRYPTO-001", "Insecure Cipher: DES",
     re.compile(r'''Cipher\.getInstance\s*\(\s*["']DES''', re.I),
     "high", FindingCategory.CRYPTO,
     "DES is cryptographically weak. Use AES-256."),
    ("JADX-CRYPTO-002", "Insecure Cipher: ECB Mode",
     re.compile(r'''Cipher\.getInstance\s*\(\s*["'][^"']*ECB''', re.I),
     "high", FindingCategory.CRYPTO,
     "ECB mode lacks semantic security. Use GCM or CBC with random IV."),
    ("JADX-CRYPTO-003", "Weak Hash: MD5",
     re.compile(r'''MessageDigest\.getInstance\s*\(\s*["']MD5["']''', re.I),
     "medium", FindingCategory.CRYPTO,
     "MD5 is broken for security. Use SHA-256 or SHA-3."),
    ("JADX-CRYPTO-004", "Weak Hash: SHA-1",
     re.compile(r'''MessageDigest\.getInstance\s*\(\s*["']SHA-?1["']''', re.I),
     "medium", FindingCategory.CRYPTO,
     "SHA-1 has collision attacks. Use SHA-256+."),
    ("JADX-CRYPTO-005", "Insecure Random",
     re.compile(r'java\.util\.Random\b'),
     "medium", FindingCategory.CRYPTO,
     "java.util.Random is not cryptographically secure. Use SecureRandom."),
    ("JADX-API-001", "Runtime Command Execution",
     re.compile(r'Runtime\.getRuntime\(\)\.exec\s*\('),
     "high", FindingCategory.CODE,
     "Runtime.exec() allows arbitrary command execution."),
    ("JADX-API-002", "JavaScript Enabled in WebView",
     re.compile(r'setJavaScriptEnabled\s*\(\s*true\s*\)'),
     "medium", FindingCategory.PLATFORM,
     "JavaScript in WebView increases XSS surface."),
    ("JADX-API-003", "WebView JavaScript Interface",
     re.compile(r'addJavascriptInterface\s*\('),
     "high", FindingCategory.PLATFORM,
     "addJavascriptInterface() exposes Java to JS, risking RCE on API<17."),
    ("JADX-API-004", "Raw SQL Query",
     re.compile(r'\.rawQuery\s*\('),
     "medium", FindingCategory.CODE,
     "Raw SQL queries risk injection. Use parameterized queries."),
    ("JADX-LOG-001", "Sensitive Data Logging",
     re.compile(r'''Log\.[dviwef]\s*\([^,]*,\s*["'][^"']*(?:password|token|key|secret)''', re.I),
     "medium", FindingCategory.STORAGE,
     "Sensitive data in system logs. Remove in production."),
    ("JADX-NET-001", "Certificate Validation Bypass",
     re.compile(r'TrustAll|AllowAll|ALLOW_ALL_HOSTNAME_VERIFIER', re.I),
     "critical", FindingCategory.NETWORK,
     "Certificate validation bypass enables MITM attacks."),
    ("JADX-NET-002", "Cleartext HTTP URL",
     re.compile(r'''["']http://[^"']+["']'''),
     "medium", FindingCategory.NETWORK,
     "Cleartext HTTP found. Use HTTPS for all communications."),
]


class JADXParser(BaseParser):
    """Parse JADX decompiled Java files for security issues."""

    RULES = _RULES

    def parse(self, data: Any) -> list[Finding]:
        findings: list[Finding] = []
        files: list[tuple[str, str]] = []

        if isinstance(data, (str, Path)):
            base_path = Path(data)
            if base_path.is_dir():
                for java_file in base_path.rglob("*.java"):
                    try:
                        content = java_file.read_text(errors="ignore")
                        files.append((str(java_file.relative_to(base_path)), content))
                    except Exception:
                        continue
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    files.append((item.get("path", "unknown"), item.get("content", "")))

        for filepath, content in files:
            for rule_id, title, pattern, severity, category, description in self.RULES:
                for match in pattern.finditer(content):
                    start = max(0, match.start() - 150)
                    end = min(len(content), match.end() + 150)
                    snippet = content[start:end].strip()

                    findings.append(Finding(
                        source=FindingSource.JADX,
                        raw_title=title,
                        raw_description=description,
                        severity=Severity(severity),
                        category=category,
                        evidence=[f"Match: {match.group(0)}", f"Context:\n{snippet[:400]}"],
                        location=filepath,
                        metadata={"rule_id": rule_id, "match": match.group(0)[:200], "file": filepath},
                    ))

        return findings
