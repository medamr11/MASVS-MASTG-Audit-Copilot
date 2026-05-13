import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Filter, Search, Download, Loader2 } from 'lucide-react'
import { getReport, type PolicyReport } from '../api/client'
import { PageHeader } from '../components/layout/Sidebar'
import ScoreGauge from '../components/charts/ScoreGauge'

const CATEGORIES = [
  'All', 'MASVS-STORAGE', 'MASVS-CRYPTO', 'MASVS-AUTH', 'MASVS-NETWORK',
  'MASVS-PLATFORM', 'MASVS-CODE', 'MASVS-RESILIENCE', 'MASVS-PRIVACY',
]
const PRIORITIES = ['All', 'P1', 'P2', 'P3', 'P4']

const SEV_BADGE: Record<string, string> = {
  critical: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
  high: 'bg-amber-500/10 text-amber-500 border border-amber-500/20',
  medium: 'bg-amber-400/10 text-amber-400 border border-amber-400/20',
  low: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  info: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
}
const PRI_BADGE: Record<string, string> = {
  P1: 'bg-rose-500/20 text-rose-500',
  P2: 'bg-amber-500/20 text-amber-500',
  P3: 'bg-amber-400/20 text-amber-400',
  P4: 'bg-emerald-500/20 text-emerald-500',
}

export default function PolicyPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [report, setReport] = useState<PolicyReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [inputJobId, setInputJobId] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('All')
  const [priorityFilter, setPriorityFilter] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    if (jobId) loadReport(jobId)
  }, [jobId])

  const loadReport = async (id: string) => {
    setLoading(true)
    try {
      const data = await getReport(id)
      setReport(data)
    } catch {}
    setLoading(false)
  }

  if (!report && !jobId) {
    return (
      <div className="max-w-xl mx-auto text-center space-y-6 py-20">
        <div className="w-24 h-24 rounded-3xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mx-auto shadow-[0_0_30px_rgba(139,92,246,0.15)]">
          <Filter className="w-12 h-12 text-violet-400 opacity-80" />
        </div>
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-violet-400">Policy Explorer</h2>
        <p className="text-slate-400 text-base">Browse the JSON policy output and filter by MASVS category or priority.</p>
        <div className="flex gap-3">
          <input type="text" value={inputJobId} onChange={e => setInputJobId(e.target.value)}
            placeholder="Enter Job ID..." className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all font-mono" />
          <button onClick={() => inputJobId && loadReport(inputJobId)} className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-xl font-bold bg-gradient-to-r from-cyan-500 to-violet-500 text-white shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] transition-all">
            Load
          </button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-24 text-slate-400 flex flex-col items-center gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-cyan-400" />
        <span className="font-medium tracking-wide">Loading Policy Data...</span>
      </div>
    )
  }

  if (!report) return <div className="text-center py-20 text-rose-400 font-medium">Policy not found.</div>

  const activeFindings = report.findings.filter(f => !f.is_duplicate)
  const filtered = activeFindings.filter(f => {
    const matchCat = categoryFilter === 'All' ||
      f.masvs_mapping?.masvs_ids?.some(id => id.startsWith(categoryFilter))
    const matchPri = priorityFilter === 'All' || f.priority === priorityFilter
    const matchSearch = !searchQuery || f.raw_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.raw_description.toLowerCase().includes(searchQuery.toLowerCase())
    return matchCat && matchPri && matchSearch
  })

  return (
    <div className="space-y-8 pb-12">
      <PageHeader title="Policy Explorer" subtitle={`${report.app.name} — MASVS v2.1.0`} />

      {/* Score Summary */}
      <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 md:p-8">
        <div className="flex flex-col md:flex-row items-center justify-between mb-8 gap-6">
          <h2 className="text-lg font-bold text-slate-200 uppercase tracking-widest">Score by Category</h2>
          <ScoreGauge score={report.score.overall || 0} size={80} label="" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(report.score.by_category || {}).map(([cat, score]) => (
            <div key={cat} className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-4 text-center hover:border-slate-700 transition-colors shadow-inner">
              <p className="text-[10px] font-bold text-slate-500 truncate uppercase tracking-widest mb-1.5">{cat.replace('MASVS-', '')}</p>
              <p className={`text-2xl font-bold tabular-nums ${
                (score as number) >= 7 ? 'text-emerald-400' : (score as number) >= 4 ? 'text-amber-400' : 'text-rose-400'
              }`}>{(score as number).toFixed(1)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 p-4 rounded-2xl bg-slate-900/30 border border-slate-800/50">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-500" />
          <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search findings by title or description..."
            className="w-full pl-12 pr-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all font-medium" />
        </div>
        <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}
          className="px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all cursor-pointer font-medium md:w-48 appearance-none">
          {CATEGORIES.map(c => <option key={c} value={c}>{c === 'All' ? '🏷️ All Categories' : c}</option>)}
        </select>
        <select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)}
          className="px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all cursor-pointer font-medium md:w-48 appearance-none">
          {PRIORITIES.map(p => <option key={p} value={p}>{p === 'All' ? '⚡ All Priorities' : p}</option>)}
        </select>
      </div>

      {/* Results count */}
      <p className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-2">{filtered.length} findings shown</p>

      {/* Findings List */}
      <div className="space-y-3">
        {filtered.map(f => (
          <div key={f.id} className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4 hover:border-slate-700 transition-all group">
            <div className="flex gap-2 shrink-0">
              <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${SEV_BADGE[f.severity] || SEV_BADGE['info']}`}>
                {f.severity}
              </span>
              <span className={`px-2 py-1 rounded-md text-[10px] font-bold border border-current/20 ${PRI_BADGE[f.priority] || PRI_BADGE['P4']}`}>
                {f.priority}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-bold text-sm text-slate-200 truncate group-hover:text-cyan-400 transition-colors">{f.raw_title}</p>
              <p className="text-xs text-slate-400 truncate mt-1">{f.raw_description.slice(0, 120)}</p>
            </div>
            <div className="flex items-center gap-4 shrink-0 w-full sm:w-auto justify-between sm:justify-end">
              <span className="text-sm font-bold text-cyan-400 tabular-nums">{f.criticality_score.toFixed(1)}</span>
              {f.masvs_mapping?.masvs_ids?.slice(0, 1).map(id => (
                <span key={id} className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-violet-500/10 text-violet-400 border border-violet-500/20">
                  {id}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Download */}
      {jobId && (
        <div className="flex justify-center pt-8 border-t border-slate-800/50">
          <a href={`/api/reports/${jobId}/policy`} download className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold border border-slate-700 bg-slate-800/50 hover:bg-slate-800 hover:border-slate-600 transition-all text-slate-200">
            <Download className="w-4 h-4" /> Download Policy JSON
          </a>
        </div>
      )}
    </div>
  )
}
