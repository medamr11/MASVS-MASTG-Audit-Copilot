import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileJson, FileCode, FileX, Shield, Loader2, Trash2, FileType } from 'lucide-react'
import { startAnalysis } from '../api/client'
import { PageHeader } from '../components/layout/Sidebar'

const FILE_TYPES: Record<string, { label: string; color: string; bg: string; icon: typeof FileJson }> = {
  apk: { label: 'Android APK', color: 'text-green-400', bg: 'bg-green-400/10', icon: Shield },
  json: { label: 'MobSF JSON', color: 'text-blue-400', bg: 'bg-blue-400/10', icon: FileJson },
  xml: { label: 'Burp / Manifest', color: 'text-amber-400', bg: 'bg-amber-400/10', icon: FileCode },
  java: { label: 'JADX Source', color: 'text-emerald-400', bg: 'bg-emerald-400/10', icon: FileCode },
  kt: { label: 'Kotlin Source', color: 'text-violet-400', bg: 'bg-violet-400/10', icon: FileCode },
}

function getFileType(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  return FILE_TYPES[ext] || { label: 'Other', color: 'text-slate-400', bg: 'bg-slate-400/10', icon: FileX }
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [files, setFiles] = useState<File[]>([])
  const [appName, setAppName] = useState('')
  const [appPackage, setAppPackage] = useState('')
  const [appVersion, setAppVersion] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = Array.from(e.dataTransfer.files)
    setFiles(prev => [...prev, ...dropped])
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setFiles(prev => [...prev, ...Array.from(e.target.files!)])
  }

  const removeFile = (idx: number) => {
    setFiles(prev => prev.filter((_, i) => i !== idx))
  }

  const handleSubmit = async () => {
    if (files.length === 0) { setError('Please upload at least one file.'); return }
    setIsLoading(true)
    setError(null)

    try {
      const result = await startAnalysis(files, appName || 'Unknown App', appPackage, appVersion)
      navigate(`/analysis/${result.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
      setIsLoading(false)
    }
  }

  const totalSize = files.reduce((sum, f) => sum + f.size, 0)

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12">
      <PageHeader
        title="New Audit"
        subtitle="Upload security artifacts to start MASVS v2 compliance analysis"
      />

      {/* Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer overflow-hidden group transition-all duration-300 ${isDragging ? 'border-cyan-400 bg-cyan-950/20 scale-[1.02]' : 'border-slate-700 hover:border-cyan-500 hover:bg-slate-900/80 bg-slate-900/50'}`}
        onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <input id="file-input" type="file" multiple className="hidden" onChange={handleFileInput}
          accept=".apk,.json,.xml,.java,.kt,.txt" />
        <div className="relative z-10 flex flex-col items-center gap-4">
          <div className={`w-20 h-20 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-inner ${
            isDragging ? 'bg-cyan-500/20 shadow-cyan-500/20' : 'bg-slate-800 shadow-black/50 group-hover:bg-cyan-950/50'
          }`}>
            <Upload className={`w-8 h-8 transition-colors ${isDragging ? 'text-cyan-400' : 'text-slate-400 group-hover:text-cyan-400'}`} />
          </div>
          <div>
            <p className="text-xl font-bold text-slate-100">Drop files here or click to browse</p>
            <p className="text-sm text-slate-400 mt-2">
              Android APK &bull; MobSF JSON &bull; Burp Suite XML &bull; AndroidManifest.xml &bull; JADX .java
            </p>
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <FileType className="w-4 h-4" />
              Uploaded Files ({files.length})
            </h3>
            <span className="text-xs text-slate-500 font-medium">{(totalSize / 1024).toFixed(1)} KB total</span>
          </div>
          <div className="space-y-2">
            {files.map((file, i) => {
              const ft = getFileType(file.name)
              const Icon = ft.icon
              return (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-950/50 border border-slate-800 group hover:border-slate-700 transition-all">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${ft.bg}`}>
                    <Icon className={`w-5 h-5 ${ft.color}`} />
                  </div>
                  <span className="flex-1 text-sm font-bold text-slate-200 truncate">{file.name}</span>
                  <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase border border-current/20 ${ft.bg} ${ft.color}`}>
                    {ft.label}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                  <button onClick={(e) => { e.stopPropagation(); removeFile(i) }}
                    className="opacity-0 group-hover:opacity-100 text-rose-400 hover:text-rose-300 hover:bg-rose-400/10 transition-all p-2 rounded-lg">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* App Metadata */}
      <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 md:p-8 space-y-5">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
          Application Details (Optional)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div>
            <label className="block text-xs font-bold text-slate-400 mb-2 tracking-wide">APP NAME</label>
            <input type="text" value={appName} onChange={e => setAppName(e.target.value)}
              placeholder="InsecureBankv2" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder-slate-600 font-medium" />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 mb-2 tracking-wide">PACKAGE NAME</label>
            <input type="text" value={appPackage} onChange={e => setAppPackage(e.target.value)}
              placeholder="com.example.app" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder-slate-600 font-medium" />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 mb-2 tracking-wide">VERSION</label>
            <input type="text" value={appVersion} onChange={e => setAppVersion(e.target.value)}
              placeholder="1.0.0" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder-slate-600 font-medium" />
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm font-medium flex items-center gap-3">
          <Shield className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={isLoading || files.length === 0}
        className="w-full inline-flex items-center justify-center gap-2 py-4 rounded-xl font-bold text-lg bg-gradient-to-r from-cyan-500 to-violet-500 text-white shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none"
      >
        {isLoading ? (
          <><Loader2 className="w-6 h-6 animate-spin" /> Analyzing Artifacts...</>
        ) : (
          <><Shield className="w-6 h-6" /> Start MASVS Audit</>
        )}
      </button>
    </div>
  )
}
