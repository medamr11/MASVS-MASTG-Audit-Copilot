import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Download, ExternalLink, Shield, Loader2, BarChart3 } from 'lucide-react'
import { getReport, getReportHtmlUrl, getReportPdfUrl, type PolicyReport } from '../api/client'
import { PageHeader } from '../components/layout/Sidebar'
import FindingCard from '../components/findings/FindingCard'
import SeverityDonut from '../components/charts/SeverityDonut'
import CoverageRadar from '../components/charts/CoverageRadar'
import ScoreGauge from '../components/charts/ScoreGauge'

export default function ReportPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [report, setReport] = useState<PolicyReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [inputJobId, setInputJobId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const activeJobId = jobId || inputJobId

  useEffect(() => {
    if (jobId) loadReport(jobId)
  }, [jobId])

  const loadReport = async (id: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getReport(id)
      setReport(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load report')
    } finally {
      setLoading(false)
    }
  }

  if (!report && !jobId) {
    return (
      <div className="max-w-xl mx-auto text-center space-y-6 py-20">
        <div className="w-24 h-24 rounded-3xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mx-auto shadow-[0_0_30px_rgba(34,211,238,0.15)]">
          <Shield className="w-12 h-12 text-cyan-400 opacity-80" />
        </div>
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-violet-400">Report Viewer</h2>
        <p className="text-slate-400 text-base">Enter a Job ID to view its report, or start a new analysis.</p>
        <div className="flex gap-3">
          <input type="text" value={inputJobId} onChange={e => setInputJobId(e.target.value)}
            placeholder="Enter Job ID..." className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all font-mono" />
          <button onClick={() => inputJobId && loadReport(inputJobId)} className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-xl font-bold bg-gradient-to-r from-cyan-500 to-violet-500 text-white shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] transition-all">
            Load
          </button>
        </div>
        {error && <p className="text-rose-400 text-sm font-medium bg-rose-500/10 p-3 rounded-xl border border-rose-500/20">{error}</p>}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-24 text-slate-400 flex flex-col items-center gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-cyan-400" />
        <span className="font-medium tracking-wide">Retrieving Audit Report...</span>
      </div>
    )
  }

  if (!report) {
    return <div className="text-center py-20 text-rose-400 font-medium">{error || 'Report not found.'}</div>
  }

  const activeFindings = report.findings.filter(f => !f.is_duplicate)
    .sort((a, b) => b.criticality_score - a.criticality_score)

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <PageHeader
        title={report.app.name}
        subtitle={`${report.app.package_name} v${report.app.version} — ${report.app.audit_date?.split('T')[0] || 'N/A'}`}
      >
        {activeJobId && (
          <div className="flex items-center gap-3">
            <a href={getReportHtmlUrl(activeJobId)} target="_blank" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl font-semibold border border-slate-700 bg-slate-800/50 hover:bg-slate-800 hover:border-slate-600 transition-all text-slate-200 text-sm">
              <ExternalLink className="w-4 h-4" /> HTML
            </a>
            <a href={getReportPdfUrl(activeJobId)} target="_blank" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl font-bold bg-gradient-to-r from-cyan-500 to-violet-500 text-white shadow-[0_0_15px_rgba(34,211,238,0.3)] hover:shadow-[0_0_25px_rgba(34,211,238,0.5)] transition-all text-sm">
              <Download className="w-4 h-4" /> PDF
            </a>
          </div>
        )}
      </PageHeader>

      {/* Stats + Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Gauge + Severity Counts */}
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 flex flex-col items-center gap-6">
          <ScoreGauge score={report.coverage_matrix.overall_score} />
          <div className="grid grid-cols-4 gap-3 w-full bg-slate-950/50 rounded-xl p-3 border border-slate-800">
            {(['critical', 'high', 'medium', 'low'] as const).map(sev => {
              const count = activeFindings.filter(f => f.severity === sev).length
              const colors: Record<string, string> = {
                critical: 'text-rose-500', high: 'text-amber-500',
                medium: 'text-amber-400', low: 'text-emerald-400',
              }
              return (
                <div key={sev} className="text-center">
                  <p className={`text-xl font-bold tabular-nums ${colors[sev]}`}>{count}</p>
                  <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider mt-0.5">{sev}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Severity Donut */}
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 flex items-center justify-center">
          <SeverityDonut findings={activeFindings} />
        </div>

        {/* Coverage Radar */}
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-4 flex flex-col">
          <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 px-2 shrink-0">
            MASVS Coverage Matrix
          </h3>
          <div className="flex-1 flex items-center justify-center">
            <CoverageRadar categories={report.coverage_matrix.categories} />
          </div>
        </div>
      </div>

      {/* Coverage Matrix Table */}
      {report.coverage_matrix.categories.length > 0 && (
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6">
          <h2 className="text-sm font-bold text-slate-200 mb-5 flex items-center gap-2 uppercase tracking-wide">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            Category Breakdown
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800">Category</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 text-center">Score</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 text-center">Tested</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 text-center">Passed</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 text-center">Failed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {report.coverage_matrix.categories.map(cat => (
                  <tr key={cat.category} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-4 font-medium text-slate-300 text-sm">{cat.category}</td>
                    <td className="px-4 py-4 text-center">
                      <span className={`font-bold text-sm px-2.5 py-1 rounded-md ${
                        cat.score >= 7 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
                        cat.score >= 4 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 
                        'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}>
                        {cat.score.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-center text-slate-400 text-sm font-mono">{cat.tested}</td>
                    <td className="px-4 py-4 text-center text-emerald-400 text-sm font-mono">{cat.passed}</td>
                    <td className="px-4 py-4 text-center text-rose-400 text-sm font-mono">{cat.failed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Executive Summary */}
      {report.executive_summary && (
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6">
          <h2 className="text-sm font-bold text-slate-200 mb-4 uppercase tracking-wide">Executive Summary</h2>
          <div className="p-5 rounded-xl bg-slate-950/50 border border-slate-800/50">
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
              {report.executive_summary}
            </p>
          </div>
        </div>
      )}

      {/* Findings */}
      <div>
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-cyan-950/50 text-cyan-400 border border-cyan-900/50">
            <Shield className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-100">
            Detailed Findings <span className="text-slate-500 font-normal text-lg ml-1">({activeFindings.length})</span>
          </h2>
        </div>
        <div className="space-y-4">
          {activeFindings.map((f, i) => <FindingCard key={f.id} finding={f} index={i} />)}
        </div>
      </div>
    </div>
  )
}
