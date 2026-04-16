'use client'
import { clsx } from 'clsx'
import {
  LayoutDashboard, Shield, Zap, BrainCircuit, FileText,
  BookOpen, GitCompare, FlaskConical, UploadCloud, ChevronRight
} from 'lucide-react'

export type Page =
  | 'dashboard'
  | 'baseline'
  | 'evaluate'
  | 'ml'
  | 'logs'
  | 'metrics'
  | 'compare'
  | 'ablation'
  | 'upload'

interface NavItem {
  id: Page
  label: string
  icon: React.ReactNode
  section?: string
}

const NAV: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard',      icon: <LayoutDashboard size={14} />,  section: 'Overview' },
  { id: 'upload',    label: 'Upload Logs',    icon: <UploadCloud size={14} />,      section: 'Data' },
  { id: 'baseline',  label: 'Baseline Infer', icon: <Shield size={14} />,           section: 'Detection' },
  { id: 'evaluate',  label: 'Live Evaluate',  icon: <Zap size={14} /> },
  { id: 'ml',        label: 'ML Anomaly',     icon: <BrainCircuit size={14} /> },
  { id: 'logs',      label: 'Access Logs',    icon: <FileText size={14} /> },
  { id: 'metrics',   label: 'Metrics',        icon: <BookOpen size={14} />,         section: 'Analysis' },
  { id: 'compare',   label: 'Compare',        icon: <GitCompare size={14} /> },
  { id: 'ablation',  label: 'Ablation Study', icon: <FlaskConical size={14} /> },
]

interface SidebarProps {
  current: Page
  onChange: (p: Page) => void
}

export function Sidebar({ current, onChange }: SidebarProps) {
  let lastSection = ''

  return (
    <aside className="w-[210px] h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-[var(--border)]">
        <div className="flex items-center gap-2.5">
          <div
            className="w-7 h-7 rounded-md flex items-center justify-center text-[11px]"
            style={{
              background: 'linear-gradient(135deg, var(--am) 0%, #e68a00 100%)',
              color: '#0b0d12',
              fontWeight: 700,
              letterSpacing: '-0.02em',
              fontFamily: 'var(--font-display)',
            }}
          >
            CG
          </div>
          <div>
            <p className="text-sm font-semibold leading-none text-[var(--tx-1)]">CloudGuard</p>
            <p className="text-[9px] font-mono text-[var(--tx-3)] mt-0.5 tracking-widest">AI SECURITY</p>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="mx-4 mt-3 mb-1 px-3 py-2 rounded-md bg-[var(--bg-2)] border border-[var(--border)] flex items-center gap-2">
        <div className="status-dot live" />
        <span className="text-[10px] font-mono text-[var(--tx-2)]">Backend connected</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-2">
        {NAV.map((item) => {
          const showSection = item.section && item.section !== lastSection
          if (item.section) lastSection = item.section

          return (
            <div key={item.id}>
              {showSection && (
                <p className="text-[9px] font-mono tracking-[0.12em] uppercase text-[var(--tx-3)] px-3 pt-4 pb-1.5">
                  {item.section}
                </p>
              )}
              <button
                onClick={() => onChange(item.id)}
                className={clsx(
                  'w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-all duration-150 group',
                  current === item.id
                    ? 'bg-[var(--am-bg)] text-[var(--am)] border border-[var(--am-border)]'
                    : 'text-[var(--tx-3)] hover:text-[var(--tx-1)] hover:bg-[var(--bg-2)]'
                )}
              >
                <span className={clsx(
                  'transition-colors',
                  current === item.id ? 'text-[var(--am)]' : 'text-[var(--tx-3)] group-hover:text-[var(--tx-2)]'
                )}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
                {current === item.id && (
                  <ChevronRight size={10} className="ml-auto opacity-60" />
                )}
              </button>
            </div>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-[var(--border)]">
        <p className="text-[9px] font-mono text-[var(--tx-3)] leading-relaxed">
          Based on OPMonitor<br />
          Wang et al., 2025
        </p>
      </div>
    </aside>
  )
}