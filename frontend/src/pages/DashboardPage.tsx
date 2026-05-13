import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { CheckCircle2, AlertCircle, Loader2, FileText, Download, ArrowRight, Activity } from 'lucide-react'
import { subscribeToEvents, type PipelineEvent } from '../api/client'
import { PageHeader } from '../components/layout/Sidebar'

const STAGES = [
  { key: 'parsing', label: 'Parsing', desc: 'Extracting findings from artifacts', icon: '📄' },
  { key: 'mapping', label: 'MASVS Mapping', desc: 'Mapping to MASVS controls', icon: '🗺️' },
  { key: 'scoring', label: 'Scoring', desc: 'Computing criticality scores', icon: '📊' },
  { key: 'deduplicating', label: 'Deduplication', desc: 'Merging duplicate findings', icon: '🔍' },
  { key: 'llm_enrichment', label: 'LLM Enrichment', desc: 'Generating remediation', icon: '🤖' },
  { key: 'report_generation', label: 'Report Gen', desc: 'Building HTML/PDF/JSON', icon: '📋' },
]

export default function DashboardPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [events, setEvents] = useState<PipelineEvent[]>([])
  const [currentStage, setCurrentStage] = useState('')
  const [progress, setProgress] = useState(0)
  const [findingCount, setFindingCount] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return
    const es = subscribeToEvents(jobId, (event) => {
      setEvents(prev => [...prev, event])
      setCurrentStage(event.stage)
      setProgress(event.progress)
      if (event.finding_count) setFindingCount(event.finding_count)
      if (event.event_type === 'complete') setIsComplete(true)
      if (event.event_type === 'error') setError(event.message)
    })
    return () => es.close()
  }, [jobId])

  const getStageStatus = (stageKey: string) => {
    const stageIdx = STAGES.findIndex(s => s.key === stageKey)
    const currentIdx = STAGES.findIndex(s => s.key === currentStage)
    if (isComplete) return 'complete'
    if (stageIdx < currentIdx) return 'complete'
    if (stageIdx === currentIdx) return 'active'
    return 'pending'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      <PageHeader
        title="Analysis Pipeline"
        subtitle={`Job: ${jobId?.slice(0, 8)}...`}
      />

      {/* Progress Card */}
      <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            <span className="text-sm font-bold text-slate-300 uppercase tracking-widest">Overall Progress</span>
          </div>
          <span className="text-lg font-bold text-cyan-400 tabular-nums">{Math.round(progress * 100)}%</span>
        </div>
        <div className="h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out bg-gradient-to-r from-cyan-500 to-violet-500 shadow-[0_0_15px_rgba(34,211,238,0.5)] relative"
            style={{ width: `${progress * 100}%` }}
          >
             <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent)] w-[200%] animate-[shimmer_2s_infinite]" />
          </div>
        </div>
        {findingCount > 0 && (
          <p className="mt-4 text-sm text-slate-400 font-medium">
            📋 <span className="text-slate-200 font-bold">{findingCount}</span> security findings detected so far
          </p>
        )}
      </div>

      {/* Pipeline Steps */}
      <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 md:p-8">
        <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-4 px-2 snap-x">
          {STAGES.map((stage, i) => {
            const status = getStageStatus(stage.key)
            return (
              <div key={stage.key} className="flex items-center shrink-0 snap-center">
                <div className="flex flex-col items-center w-20">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-2xl border transition-all duration-500 ${
                    status === 'complete' ? 'bg-emerald-500/10 border-emerald-500/30' :
                    status === 'active' ? 'bg-cyan-500/10 border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.2)] animate-pulse' :
                    'bg-slate-950 border-slate-800 opacity-50 grayscale'
                  }`}>
                    {status === 'complete' ? <CheckCircle2 className="w-6 h-6 text-emerald-400" /> : stage.icon}
                  </div>
                  <span className={`text-[10px] mt-3 font-bold text-center tracking-wider uppercase ${
                    status === 'active' ? 'text-cyan-400' :
                    status === 'complete' ? 'text-emerald-400' :
                    'text-slate-500'
                  }`}>{stage.label}</span>
                </div>
                {i < STAGES.length - 1 && (
                  <div className="w-8 md:w-16 h-[2px] bg-slate-800 mx-1 md:mx-2 relative overflow-hidden rounded-full shrink-0">
                     {status === 'complete' && <div className="absolute inset-0 bg-emerald-500/50" />}
                     {status === 'active' && <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500 to-transparent w-[200%] animate-[shimmer_2s_infinite]" />}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Stage Details */}
        <div className="space-y-2">
          {STAGES.map((stage) => {
            const status = getStageStatus(stage.key)
            if (status === 'pending') return null
            return (
              <div key={stage.key} className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
                status === 'active' ? 'bg-cyan-950/30 border border-cyan-800/50 shadow-inner' :
                status === 'complete' ? 'bg-slate-950/50 border border-transparent' : ''
              }`}>
                <span className="text-2xl">{stage.icon}</span>
                <div className="flex-1">
                  <p className="text-sm font-bold text-slate-200">{stage.label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{stage.desc}</p>
                </div>
                {status === 'complete' && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                {status === 'active' && <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />}
              </div>
            )
          })}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-rose-950/30 border border-rose-900/50 rounded-2xl p-6">
          <div className="flex items-center gap-3 text-rose-400 mb-2">
            <AlertCircle className="w-6 h-6" />
            <span className="font-bold text-lg">Pipeline Error</span>
          </div>
          <p className="text-sm text-rose-300/80 leading-relaxed font-mono">{error}</p>
        </div>
      )}

      {/* Completion */}
      {isComplete && (
        <div className="bg-slate-900/50 backdrop-blur-xl border border-emerald-500/30 rounded-2xl p-8 space-y-6 shadow-[0_0_30px_rgba(16,185,129,0.1)]">
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle2 className="w-8 h-8" />
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">Audit Complete!</span>
          </div>
          <p className="text-slate-300 text-lg">
            <strong className="text-white">{findingCount}</strong> findings analyzed and successfully mapped to MASVS v2 controls.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link to={`/report/${jobId}`} className="inline-flex items-center justify-center gap-2 py-3.5 rounded-xl font-bold bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] transition-all hover:-translate-y-0.5">
              <FileText className="w-5 h-5" /> View Report
            </Link>
            <a href={`/api/reports/${jobId}/html`} target="_blank"
              className="inline-flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold border border-slate-700 bg-slate-800/50 hover:bg-slate-800 hover:border-slate-600 transition-all text-slate-200">
              <Download className="w-5 h-5" /> Download HTML
            </a>
            <Link to={`/policy/${jobId}`} className="inline-flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold border border-slate-700 bg-slate-800/50 hover:bg-slate-800 hover:border-slate-600 transition-all text-slate-200">
              <ArrowRight className="w-5 h-5" /> Policy Explorer
            </Link>
          </div>
        </div>
      )}

      {/* Event Log */}
      {events.length > 0 && (
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Event Log</h3>
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
            {events.map((e, i) => (
              <div key={i} className="text-xs text-slate-400 font-mono py-1 flex gap-3">
                <span className="text-cyan-500 shrink-0 opacity-70">[{e.stage}]</span>
                <span className="text-slate-300">{e.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
