"""
Unit tests for all parsers.
"""

import json
import pytest
from pathlib import Path

from app.parsers.mobsf import MobSFParser
from app.parsers.jadx import JADXParser
from app.parsers.burp import BurpParser
from app.parsers.manifest import ManifestParser
from app.parsers.normalizer import FindingNormalizer
from app.models.schemas import Severity, FindingSource


# ── Fixtures ─────────────────────────────────────────────────────

SAMPLE_MOBSF = {
    "app_name": "TestApp",
    "package_name": "com.test.app",
    "code_analysis": {
        "hardcoded_secret": {
            "metadata": {
                "severity": "high",
                "description": "Hardcoded API key found in source code."
            },
            "files": {"com/test/Config.java": "Line 12"}
        }
    },
    "manifest_analysis": [
        {
            "title": "App is debuggable",
            "severity": "high",
            "description": "android:debuggable is set to true.",
            "component": "application"
        }
    ],
    "network_security": [
        {
            "title": "Cleartext traffic allowed",
            "severity": "high",
            "description": "The app allows cleartext HTTP traffic."
        }
    ],
    "permissions": {
        "android.permission.CAMERA": {"description": "Camera access", "status": "dangerous"},
        "android.permission.INTERNET": {"description": "Internet access", "status": "normal"},
    },
    "certificate_analysis": {
        "certificate_findings": [
            {"title": "Weak signature", "severity": "medium", "description": "SHA-1 signature"}
        ]
    }
}

SAMPLE_MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.test.app">
    <uses-sdk android:minSdkVersion="19" android:targetSdkVersion="28" />
    <application
        android:debuggable="true"
        android:allowBackup="true"
        android:usesCleartextTraffic="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
            </intent-filter>
        </activity>
        <service android:name=".MyService" android:exported="true" />
        <provider android:name=".DataProvider" android:exported="true" />
    </application>
    <permission android:name="com.test.PERM" android:protectionLevel="normal" />
</manifest>"""

SAMPLE_BURP = """<?xml version="1.0"?>
<issues>
    <issue>
        <serialNumber>1</serialNumber>
        <type>1049600</type>
        <name>Cross-site scripting (reflected)</name>
        <host>https://api.example.com</host>
        <path>/search</path>
        <severity>High</severity>
        <confidence>Certain</confidence>
        <issueBackground>XSS occurs when user input is included in the page without proper encoding.</issueBackground>
        <issueDetail>The parameter 'q' is reflected in the response.</issueDetail>
    </issue>
    <issue>
        <serialNumber>2</serialNumber>
        <name>TLS certificate not trusted</name>
        <host>https://api.example.com</host>
        <path>/</path>
        <severity>Medium</severity>
        <confidence>Firm</confidence>
        <issueDetail>The server TLS certificate is not trusted.</issueDetail>
    </issue>
</issues>"""

SAMPLE_JAVA = """
package com.test.app;

import java.util.Random;
import javax.crypto.Cipher;

public class CryptoHelper {
    private static final String API_KEY = "sk-1234567890abcdef1234";
    private static final String PASSWORD = "SuperSecret123";

    public void encrypt(byte[] data) {
        Cipher cipher = Cipher.getInstance("DES/ECB/PKCS5Padding");
        Random random = new Random();
    }

    public void doRequest() {
        String url = "http://api.example.com/data";
        Runtime.getRuntime().exec("ls -la");
    }
}
"""


# ── Tests ────────────────────────────────────────────────────────

class TestMobSFParser:
    def test_parse_basic(self):
        parser = MobSFParser()
        findings = parser.parse(SAMPLE_MOBSF)
        assert len(findings) > 0

    def test_code_analysis(self):
        parser = MobSFParser()
        findings = parser.parse(SAMPLE_MOBSF)
        code_findings = [f for f in findings if f.metadata.get("section") == "code_analysis"]
        assert len(code_findings) >= 1

    def test_manifest_analysis(self):
        parser = MobSFParser()
        findings = parser.parse(SAMPLE_MOBSF)
        manifest_findings = [f for f in findings if f.metadata.get("section") == "manifest_analysis"]
        assert len(manifest_findings) >= 1

    def test_severity_mapping(self):
        parser = MobSFParser()
        findings = parser.parse(SAMPLE_MOBSF)
        severities = {f.severity for f in findings}
        assert Severity.HIGH in severities or Severity.MEDIUM in severities

    def test_permissions(self):
        parser = MobSFParser()
        findings = parser.parse(SAMPLE_MOBSF)
        perm_findings = [f for f in findings if f.metadata.get("section") == "permissions"]
        assert len(perm_findings) >= 1  # CAMERA is dangerous

    def test_source_is_mobsf(self):
        parser = MobSFParser()
        findings = parser.parse(SAMPLE_MOBSF)
        assert all(f.source == FindingSource.MOBSF for f in findings)

    def test_idempotent(self):
        parser = MobSFParser()
        r1 = parser.parse(SAMPLE_MOBSF)
        r2 = parser.parse(SAMPLE_MOBSF)
        assert len(r1) == len(r2)
        assert [f.raw_title for f in r1] == [f.raw_title for f in r2]


class TestManifestParser:
    def test_parse_basic(self):
        parser = ManifestParser()
        findings = parser.parse(SAMPLE_MANIFEST)
        assert len(findings) > 0

    def test_debuggable(self):
        parser = ManifestParser()
        findings = parser.parse(SAMPLE_MANIFEST)
        debug = [f for f in findings if "debuggable" in f.raw_title.lower()]
        assert len(debug) >= 1
        assert debug[0].severity == Severity.HIGH

    def test_allow_backup(self):
        parser = ManifestParser()
        findings = parser.parse(SAMPLE_MANIFEST)
        backup = [f for f in findings if "backup" in f.raw_title.lower()]
        assert len(backup) >= 1

    def test_cleartext(self):
        parser = ManifestParser()
        findings = parser.parse(SAMPLE_MANIFEST)
        ct = [f for f in findings if "cleartext" in f.raw_title.lower()]
        assert len(ct) >= 1

    def test_exported_components(self):
        parser = ManifestParser()
        findings = parser.parse(SAMPLE_MANIFEST)
        exported = [f for f in findings if "exported" in f.raw_title.lower()]
        assert len(exported) >= 2  # service + provider

    def test_sdk_versions(self):
        parser = ManifestParser()
        findings = parser.parse(SAMPLE_MANIFEST)
        sdk = [f for f in findings if "sdk" in f.raw_title.lower()]
        assert len(sdk) >= 1  # minSdk 19 < 23


class TestBurpParser:
    def test_parse_basic(self):
        parser = BurpParser()
        findings = parser.parse(SAMPLE_BURP)
        assert len(findings) == 2

    def test_severity(self):
        parser = BurpParser()
        findings = parser.parse(SAMPLE_BURP)
        assert findings[0].severity == Severity.HIGH
        assert findings[1].severity == Severity.MEDIUM

    def test_location(self):
        parser = BurpParser()
        findings = parser.parse(SAMPLE_BURP)
        assert "api.example.com" in (findings[0].location or "")


class TestJADXParser:
    def test_parse_basic(self):
        parser = JADXParser()
        files = [{"path": "CryptoHelper.java", "content": SAMPLE_JAVA}]
        findings = parser.parse(files)
        assert len(findings) > 0

    def test_hardcoded_key(self):
        parser = JADXParser()
        findings = parser.parse([{"path": "test.java", "content": SAMPLE_JAVA}])
        key_findings = [f for f in findings if "api key" in f.raw_title.lower() or "password" in f.raw_title.lower()]
        assert len(key_findings) >= 1

    def test_des_cipher(self):
        parser = JADXParser()
        findings = parser.parse([{"path": "test.java", "content": SAMPLE_JAVA}])
        des = [f for f in findings if "des" in f.raw_title.lower() or "ecb" in f.raw_title.lower()]
        assert len(des) >= 1

    def test_http_url(self):
        parser = JADXParser()
        findings = parser.parse([{"path": "test.java", "content": SAMPLE_JAVA}])
        http = [f for f in findings if "http" in f.raw_title.lower() or "cleartext" in f.raw_title.lower()]
        assert len(http) >= 1


class TestNormalizer:
    def test_detect_mobsf(self):
        content = json.dumps(SAMPLE_MOBSF)
        assert FindingNormalizer.detect_type("report.json", content) == "mobsf"

    def test_detect_manifest(self):
        assert FindingNormalizer.detect_type("AndroidManifest.xml", SAMPLE_MANIFEST) == "manifest"

    def test_detect_burp(self):
        assert FindingNormalizer.detect_type("burp_export.xml", SAMPLE_BURP) == "burp"

    def test_detect_java(self):
        assert FindingNormalizer.detect_type("Test.java", SAMPLE_JAVA) == "jadx"
