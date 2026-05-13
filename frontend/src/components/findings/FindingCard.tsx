import { useState } from 'react'
import { ChevronDown, ChevronUp, MapPin, Code2, Lightbulb } from 'lucide-react'
import type { Finding } from '../../api/client'

const SEVERITY_BADGE: Record<string, string> = {
  critical: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
  high: 'bg-amber-500/10 text-amber-500 border border-amber-500/20',
  medium: 'bg-amber-400/10 text-amber-400 border border-amber-400/20',
  low: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  info: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
}

const PRIORITY_BADGE: Record<string, string> = {
  P1: 'bg-rose-500/20 text-rose-500',
  P2: 'bg-amber-500/20 text-amber-500',
  P3: 'bg-amber-400/20 text-amber-400',
  P4: 'bg-emerald-500/20 text-emerald-500',
}

export default function FindingCard({ finding, index = 0 }: { finding: Finding; index?: number }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div
      className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl overflow-hidden shadow-[0_0_15px_rgba(0,0,0,0.2)]"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 flex items-center gap-4 text-left hover:bg-slate-800/50 transition-colors group"
      >
        <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${SEVERITY_BADGE[finding.severity] || SEVERITY_BADGE['info']}`}>
          {finding.severity}
        </span>
        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border border-current/20 hidden sm:inline-block ${PRIORITY_BADGE[finding.priority] || PRIORITY_BADGE['P4']}`}>
          {finding.priority}
        </span>
        <span className="flex-1 font-bold text-sm text-slate-200 truncate group-hover:text-cyan-400 transition-colors">{finding.raw_title}</span>
        <span className="text-sm font-bold text-cyan-400 tabular-nums">
          {finding.criticality_score.toFixed(1)}
        </span>
        {finding.masvs_mapping?.masvs_ids?.slice(0, 2).map(id => (
          <span key={id} className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-violet-500/10 text-violet-400 border border-violet-500/20 hidden md:inline">
            {id}
          </span>
        ))}
        <div className="w-6 h-6 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center shrink-0">
          {isOpen ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </button>

      {isOpen && (
        <div className="px-4 pb-4 space-y-5 border-t border-slate-800/50 pt-4 bg-slate-950/20">
          <p className="text-sm text-slate-300 leading-relaxed">
            {finding.raw_description}
          </p>

          {finding.location && (
            <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/50">
              <MapPin className="w-4 h-4 text-cyan-500 shrink-0" />
              <span className="font-mono truncate">{finding.location}</span>
            </div>
          )}

          {/* Score Breakdown */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Impact', value: finding.impact, color: 'text-rose-500', bg: 'bg-rose-500' },
              { label: 'Exploitability', value: finding.exploitability, color: 'text-amber-500', bg: 'bg-amber-500' },
              { label: 'Exposure', value: finding.exposure, color: 'text-blue-500', bg: 'bg-blue-500' },
            ].map(({ label, value, color, bg }) => (
              <div key={label} className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-3 text-center shadow-inner">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">{label}</p>
                <div className="flex items-end justify-center gap-1">
                  <span className={`text-2xl font-bold ${color}`}>{value}</span>
                  <span className="text-xs text-slate-600 pb-1">/5</span>
                </div>
                <div className="mt-2 h-1.5 rounded-full bg-slate-900 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${bg}`}
                    style={{ width: `${(value / 5) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Evidence */}
          {finding.evidence?.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Code2 className="w-4 h-4 text-slate-500" />
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Evidence</p>
              </div>
              {finding.evidence.slice(0, 2).map((ev, i) => (
                <pre key={i} className="text-xs bg-slate-950 p-4 rounded-xl overflow-x-auto text-slate-300 mb-2 font-mono border border-slate-800 shadow-inner">
                  {ev.slice(0, 400)}
                </pre>
              ))}
            </div>
          )}

          {/* Remediation */}
          {finding.remediation && (
            <div className="bg-emerald-500/10 border-l-2 border-emerald-500 p-5 rounded-r-xl rounded-l-sm mt-6">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="w-5 h-5 text-emerald-400" />
                <p className="text-sm font-bold text-emerald-400 uppercase tracking-wider">Remediation</p>
              </div>
              <p className="text-sm text-slate-200 font-bold mb-3">{finding.remediation.short_fix}</p>
              {finding.remediation.detailed_steps?.length > 0 && (
                <ul className="mt-3 space-y-2">
                  {finding.remediation.detailed_steps.map((s, i) => (
                    <li key={i} className="text-sm text-slate-300 flex gap-3">
                      <span className="text-emerald-500 font-bold">›</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              )}
              {finding.remediation.code_example && (
                <pre className="mt-4 text-xs bg-slate-950 p-4 rounded-xl overflow-x-auto font-mono border border-emerald-500/20 text-emerald-100 shadow-inner">
                  {finding.remediation.code_example}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
