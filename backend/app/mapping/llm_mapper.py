"""
LLM-based semantic mapper.
Layer 2: Gemini API fallback for findings with low rule confidence.
"""

import json

from app.models.schemas import Finding, MASVSMapping
from app.core.logging import get_logger

logger = get_logger(__name__)

MAPPING_SYSTEM_PROMPT = """You are an expert mobile security auditor specializing in OWASP MASVS v2.1.0.

Given a security finding from a mobile app audit, map it to the appropriate MASVS controls, MASWE weaknesses, and MASTG test cases.

MASVS v2.1.0 Categories:
- MASVS-STORAGE: Secure storage of sensitive data at rest
- MASVS-CRYPTO: Cryptographic best practices
- MASVS-AUTH: Authentication and authorization mechanisms
- MASVS-NETWORK: Secure network communication (data in transit)
- MASVS-PLATFORM: Secure interaction with the mobile platform and IPC
- MASVS-CODE: Code quality and security best practices
- MASVS-RESILIENCE: Resilience against reverse engineering and tampering
- MASVS-PRIVACY: Privacy controls and data minimization

Respond ONLY with a JSON object in this exact format:
{
  "maswe_ids": ["MASWE-XXXX"],
  "masvs_ids": ["MASVS-CATEGORY-N"],
  "mastg_tests": ["MASTG-TEST-XXXX"],
  "rationale": "Brief explanation of the mapping",
  "confidence": 0.85
}"""


async def llm_map_finding(finding: Finding, gemini_client) -> MASVSMapping:
    """
    Use Gemini to semantically map a finding to MASVS controls.

    Args:
        finding: The finding to map
        gemini_client: An initialized Gemini API client

    Returns:
        MASVSMapping with LLM-inferred mappings
    """
    try:
        prompt = f"""Map this mobile security finding to MASVS v2.1.0 controls:

Title: {finding.raw_title}
Description: {finding.raw_description[:600]}
Category: {finding.category.value}
Severity: {finding.severity.value}
Evidence: {' | '.join(finding.evidence[:2])[:400]}
Location: {finding.location or 'N/A'}"""

        response = await gemini_client.send_message(
            system_prompt=MAPPING_SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=500,
        )

        # Parse JSON response
        result = json.loads(response)

        return MASVSMapping(
            maswe_ids=result.get("maswe_ids", []),
            masvs_ids=result.get("masvs_ids", []),
            mastg_tests=result.get("mastg_tests", []),
            confidence=min(float(result.get("confidence", 0.7)), 1.0),
            rationale=result.get("rationale", "LLM-inferred mapping"),
            mapping_source="llm",
        )

    except Exception as e:
        logger.error("llm_mapping_failed", finding_id=finding.id, error=str(e))
        return MASVSMapping(confidence=0.0, mapping_source="llm")
