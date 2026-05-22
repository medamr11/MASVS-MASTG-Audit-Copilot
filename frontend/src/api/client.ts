/**
 * API client for the MASVS Audit Copilot backend.
 */

const API_BASE = '/api';

export interface JobResponse {
  job_id: string;
  status: string;
  progress: number;
  current_stage: string;
  finding_count: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface PipelineEvent {
  event_type: string;
  stage: string;
  progress: number;
  message: string;
  finding_count: number;
  data: Record<string, unknown>;
}

export interface Finding {
  id: string;
  source: string;
  raw_title: string;
  raw_description: string;
  severity: string;
  category: string;
  evidence: string[];
  location: string | null;
  criticality_score: number;
  priority: string;
  impact: number;
  exploitability: number;
  exposure: number;
  is_duplicate: boolean;
  masvs_mapping: {
    masvs_ids: string[];
    maswe_ids: string[];
    mastg_tests: string[];
    confidence: number;
    rationale: string;
  } | null;
  remediation: {
    short_fix: string;
    detailed_steps: string[];
    code_example: string | null;
    references: string[];
  } | null;
}

export interface PolicyReport {
  app: { name: string; package_name: string; version: string; audit_date: string; };
  score: { overall: number; by_category: Record<string, number> };
  findings: Finding[];
  coverage_matrix: {
    categories: { category: string; score: number; tested: number; passed: number; failed: number; not_tested: number }[];
    overall_score: number;
  };
  executive_summary: string;
}

export async function startAnalysis(files: File[], appName: string, appPackage: string, appVersion: string): Promise<JobResponse> {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));
  formData.append('app_name', appName);
  formData.append('app_package', appPackage);
  formData.append('app_version', appVersion);

  const res = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: formData });
  if (!res.ok) {
    let errorDetail = `Analysis failed: ${res.status}`;
    try {
      const errorData = await res.json();
      if (errorData.detail) {
        errorDetail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch (e) {
      // Ignore JSON parse error, fallback to status
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Job not found: ${res.status}`);
  return res.json();
}

export function subscribeToEvents(jobId: string, onEvent: (event: PipelineEvent) => void): EventSource {
  const es = new EventSource(`${API_BASE}/jobs/${jobId}/events`);

  es.addEventListener('stage_update', (e) => onEvent(JSON.parse(e.data)));
  es.addEventListener('complete', (e) => { onEvent(JSON.parse(e.data)); es.close(); });
  es.addEventListener('error', (e) => {
    if ((e as MessageEvent).data) onEvent(JSON.parse((e as MessageEvent).data));
    es.close();
  });

  return es;
}

export async function getReport(jobId: string): Promise<PolicyReport> {
  const res = await fetch(`${API_BASE}/reports/${jobId}`);
  if (!res.ok) throw new Error(`Report not found: ${res.status}`);
  return res.json();
}

export function getReportHtmlUrl(jobId: string): string {
  return `${API_BASE}/reports/${jobId}/html`;
}

export function getReportPdfUrl(jobId: string): string {
  return `${API_BASE}/reports/${jobId}/pdf`;
}

export function getReportPolicyUrl(jobId: string): string {
  return `${API_BASE}/reports/${jobId}/policy`;
}
