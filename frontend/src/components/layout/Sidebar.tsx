import { type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Shield, Upload, FileText, Filter, Home, Menu, X
} from 'lucide-react'

const navSections = [
  {
    title: 'Main',
    items: [
      { path: '/', label: 'Home', icon: Home },
      { path: '/upload', label: 'New Audit', icon: Upload },
    ],
  },
  {
    title: 'Results',
    items: [
      { path: '/report', label: 'Reports', icon: FileText },
      { path: '/policy', label: 'Policy Explorer', icon: Filter },
    ],
  },
]

export function Sidebar({ isOpen, onClose }: { isOpen?: boolean, onClose?: () => void }) {
  const location = useLocation()

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-40 md:hidden transition-opacity"
          onClick={onClose}
        />
      )}
      
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        {/* Mobile Close Button */}
        {onClose && (
          <button 
            onClick={onClose}
            className="md:hidden absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-50 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
        
        {/* Logo */}
        <div className="p-6">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-violet-500 flex items-center justify-center shadow-[0_0_15px_rgba(34,211,238,0.3)] group-hover:shadow-[0_0_25px_rgba(34,211,238,0.5)] transition-shadow">
              <Shield className="w-5 h-5 text-slate-950" />
            </div>
            <div>
              <span className="text-sm font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-violet-400">MASVS Audit</span>
              <span className="block text-[10px] text-slate-500 font-medium tracking-widest uppercase">Copilot</span>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-6 overflow-y-auto">
          {navSections.map((section) => (
            <div key={section.title}>
              <p className="px-3 mb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
                {section.title}
              </p>
              <div className="space-y-1">
                {section.items.map(({ path, label, icon: Icon }) => {
                  const isActive = location.pathname === path ||
                    (path !== '/' && location.pathname.startsWith(path))
                  return (
                    <Link
                      key={path}
                      to={path}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors relative ${isActive ? 'text-cyan-400 bg-cyan-400/10' : 'text-slate-400 hover:text-slate-50 hover:bg-slate-800/50'}`}
                    >
                      {isActive && (
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-cyan-400 rounded-r-full" />
                      )}
                      <Icon className="w-5 h-5" />
                      <span>{label}</span>
                    </Link>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Bottom status */}
        <div className="p-4 border-t border-slate-800/50">
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-950/50">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-slate-400">MASVS v2.1.0 Active</span>
          </div>
        </div>
      </aside>
    </>
  )
}

export function PageContainer({ children, onMenuClick }: { children: ReactNode, onMenuClick?: () => void }) {
  return (
    <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950">
      {/* Mobile Header */}
      <header className="md:hidden shrink-0 flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-cyan-400" />
          <span className="font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 text-lg">MASVS Copilot</span>
        </div>
        {onMenuClick && (
          <button onClick={onMenuClick} className="p-2 text-slate-400 hover:text-slate-50 transition-colors">
            <Menu className="w-6 h-6" />
          </button>
        )}
      </header>

      {/* Main scrollable area */}
      <div className="flex-1 overflow-y-auto">
        <main className="p-4 md:p-8 max-w-[1400px] mx-auto w-full min-h-[calc(100%-60px)]">
          {children}
        </main>
        <footer className="border-t border-slate-800/50 py-4 px-4 md:px-8 text-center shrink-0">
          <p className="text-xs text-slate-500">
            MASVS Audit Copilot — OWASP MASVS v2.1.0 Compliance Engine
          </p>
        </footer>
      </div>
    </div>
  )
}

export function PageHeader({ title, subtitle, children }: {
  title: string
  subtitle?: string
  children?: ReactNode
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
      <div>
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-violet-400 to-cyan-400 bg-[length:200%_auto] animate-[shimmer_3s_linear_infinite]">{title}</h1>
        {subtitle && (
          <p className="text-slate-400 mt-1.5 text-sm">{subtitle}</p>
        )}
      </div>
      {children && <div className="flex items-center gap-3 shrink-0">{children}</div>}
    </div>
  )
}
