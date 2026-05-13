"""
LLM prompt templates for report generation.
"""

DEDUP_SYSTEM = """You are a security finding deduplication expert. Analyze the provided findings and identify duplicates.
Group findings that describe the same underlying vulnerability, even if they have different titles or come from different tools.
Respond ONLY with a JSON array of duplicate group objects."""

DEDUP_USER = """Analyze these security findings and identify duplicate groups.
For each group, list the finding IDs that should be merged.

Findings:
{findings_text}

Respond with JSON:
[
  {{"group_id": "group_1", "finding_ids": ["id1", "id2"], "merged_title": "Best title for the group", "rationale": "Why these are duplicates"}}
]

Only include groups with 2+ findings. Findings not in any group are unique."""

EXEC_SUMMARY_SYSTEM = """You are a senior mobile security auditor writing for a CISO audience.
Write a professional executive summary that is clear, actionable, and highlights business risk.
Use formal language. Do not use markdown headers in your response — write flowing prose paragraphs."""

EXEC_SUMMARY_USER = """Write a 3-5 paragraph executive summary for this mobile application security audit.

Application: {app_name} ({app_package})
Audit Date: {audit_date}
Platform: {platform}

Overall Score: {overall_score}/10
Total Findings: {total_findings}
Critical: {critical_count} | High: {high_count} | Medium: {medium_count} | Low: {low_count}

MASVS Coverage:
{coverage_text}

Top 10 Findings:
{top_findings}

Write the executive summary now. Focus on business risk and key recommendations."""

REMEDIATION_SYSTEM = """You are a mobile security remediation expert. Provide specific, actionable remediation guidance.
Include concrete code examples when relevant. Reference OWASP standards.
Respond ONLY with JSON."""

REMEDIATION_USER = """Provide remediation guidance for this security finding:

Finding: {title}
Description: {description}
Severity: {severity}
Category: {category}
Evidence: {evidence}
MASVS IDs: {masvs_ids}

Relevant Knowledge Base Context:
{rag_context}

Respond with JSON:
{{
  "short_fix": "One-sentence fix description",
  "detailed_steps": ["Step 1", "Step 2", ...],
  "code_example": "Code fix example or null",
  "references": ["CWE-XXX", "URL", ...]
}}"""
