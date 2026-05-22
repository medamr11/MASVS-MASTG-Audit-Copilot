import { Link } from 'react-router-dom'
import {
  Upload, FileText, Zap, Database,
  Brain, BarChart3, Lock, Eye, ArrowRight, Cpu,
  FileJson, FileCode, Globe, Shield
} from 'lucide-react'

const features = [
  {
    icon: Database,
    title: 'Multi-Source Parsing',
    desc: 'APK direct upload via MobSF, JADX, Burp Suite, Manifest — all auto-detected.',
    color: 'text-cyan-400',
    bg: 'bg-cyan-400/10',
  },
  {
    icon: Brain,
    title: 'AI-Powered Mapping',
    desc: 'Gemini LLM maps findings to MASVS v2.1.0 controls automatically.',
    color: 'text-violet-400',
    bg: 'bg-violet-400/10',
  },
  {
    icon: BarChart3,
    title: 'Criticality Scoring',
    desc: 'Impact × Exploitability × Exposure model with keyword refinement.',
    color: 'text-amber-400',
    bg: 'bg-amber-400/10',
  },
  {
    icon: Lock,
    title: 'RAG Remediation',
    desc: 'Context-aware fix guidance from the OWASP knowledge base.',
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
  },
]

const fileTypes = [
  { icon: Shield, label: 'Android APK', ext: '.apk', color: 'text-green-400', bg: 'bg-green-400/10' },
  { icon: FileJson, label: 'MobSF JSON', ext: '.json', color: 'text-blue-400', bg: 'bg-blue-400/10' },
  { icon: FileCode, label: 'Burp Suite XML', ext: '.xml', color: 'text-amber-400', bg: 'bg-amber-400/10' },
  { icon: FileCode, label: 'AndroidManifest', ext: '.xml', color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
  { icon: Globe, label: 'JADX Java', ext: '.java', color: 'text-violet-400', bg: 'bg-violet-400/10' },
]

export default function HomePage() {
  return (
    <div className="space-y-12 pb-12">
      {/* Hero */}
      <div className="text-center py-16 px-4">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-950/50 border border-cyan-800/50 text-cyan-400 text-xs font-bold tracking-widest mb-8 shadow-[0_0_15px_rgba(34,211,238,0.15)]">
          <Zap className="w-3.5 h-3.5" />
          AI-POWERED MOBILE SECURITY AUDITING
        </div>
        <h1 className="text-5xl md:text-7xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-violet-400 to-cyan-400 leading-tight mb-6 pb-2">
          MASVS Audit<br className="hidden sm:block" /> Copilot
        </h1>
        <p className="text-slate-400 text-lg md:text-xl max-w-3xl mx-auto leading-relaxed">
          Transform raw security analysis artifacts into structured, professional
          OWASP MASVS v2 audit reports — powered by Gemini AI and RAG-augmented remediation.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-5 mt-10">
          <Link to="/upload" className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-bold bg-gradient-to-r from-cyan-500 to-violet-500 text-white shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] hover:-translate-y-0.5 transition-all w-full sm:w-auto">
            <Upload className="w-5 h-5" />
            Start New Audit
          </Link>
          <Link to="/report" className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-semibold border border-slate-700 bg-slate-800/50 hover:bg-slate-800 hover:border-slate-600 transition-all text-slate-200 w-full sm:w-auto">
            <FileText className="w-5 h-5" />
            View Reports
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 mb-6 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-950/50 text-cyan-400">
            <Cpu className="w-5 h-5" />
          </div>
          Pipeline Capabilities
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map((feat) => (
            <div key={feat.title} className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 group hover:border-slate-700 transition-all">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 transition-transform group-hover:scale-110 ${feat.bg}`}>
                <feat.icon className={`w-6 h-6 ${feat.color}`} />
              </div>
              <h3 className="font-bold text-base text-slate-100 mb-2">{feat.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{feat.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Supported File Types */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 mb-6 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-violet-950/50 text-violet-400">
            <Eye className="w-5 h-5" />
          </div>
          Supported Artifact Types
        </h2>
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 md:p-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {fileTypes.map((ft) => (
              <div key={ft.label} className="flex items-center gap-4 p-4 rounded-xl bg-slate-950/50 border border-slate-800 hover:border-slate-700 transition-all">
                <div className={`w-10 h-10 rounded-lg flex shrink-0 items-center justify-center ${ft.bg}`}>
                  <ft.icon className={`w-5 h-5 ${ft.color}`} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-slate-200 truncate">{ft.label}</p>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">{ft.ext}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-sm text-slate-500 mt-6 text-center font-medium">
            Upload an APK for automatic MobSF analysis, or combine multiple artifact files for a comprehensive cross-source audit.
          </p>
        </div>
      </div>

      {/* Pipeline Flow */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 mb-6 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-950/50 text-cyan-400">
            <ArrowRight className="w-5 h-5" />
          </div>
          Audit Pipeline
        </h2>
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-8">
          <div className="flex items-center justify-between gap-2 overflow-x-auto pb-4 px-2 snap-x">
            {[
              { label: 'Parse', emoji: '📄' },
              { label: 'Map', emoji: '🗺️' },
              { label: 'Score', emoji: '📊' },
              { label: 'Dedup', emoji: '🔍' },
              { label: 'Enrich', emoji: '🤖' },
              { label: 'Report', emoji: '📋' },
            ].map((step, i, arr) => (
              <div key={step.label} className="flex items-center shrink-0 snap-center">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-center text-2xl shadow-inner shadow-black/50">
                    {step.emoji}
                  </div>
                  <span className="text-xs font-bold text-slate-400 tracking-wider uppercase">{step.label}</span>
                </div>
                {i < arr.length - 1 && (
                  <div className="w-8 md:w-16 h-[2px] bg-slate-800 mx-2 md:mx-4 relative overflow-hidden rounded-full">
                     <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500 to-transparent w-[200%] animate-[shimmer_2s_infinite]" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
