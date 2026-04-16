'use client'
import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

// ── Badge / Tag ────────────────────────────────────────────────
type TagVariant = 'red' | 'green' | 'amber' | 'blue' | 'orange' | 'muted'

const TAG_MAP: Record<string, TagVariant> = {
  critical: 'red', high: 'orange', medium: 'amber', low: 'green',
  'over-granted': 'red', allowed: 'green', normal: 'green',
}

export function Tag({ label, variant }: { label: string; variant?: TagVariant }) {
  const v = variant ?? TAG_MAP[label.toLowerCase()] ?? 'muted'
  return <span className={`tag tag-${v}`}>{label}</span>
}

export function RiskTag({ risk }: { risk: string }) {
  return <Tag label={risk} />
}

export function VerdictTag({ verdict }: { verdict: string }) {
  return <Tag label={verdict.replace('-', ' ')} variant={verdict === 'over-granted' ? 'red' : 'green'} />
}

// ── Button ─────────────────────────────────────────────────────
interface BtnProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md'
  loading?: boolean
  icon?: React.ReactNode
}

export function Btn({ variant = 'outline', size = 'md', loading, icon, children, className, ...rest }: BtnProps) {
  const base = 'inline-flex items-center gap-2 font-sans font-medium rounded-lg transition-all duration-150 focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed'
  const sizes = { sm: 'text-xs px-3 py-1.5', md: 'text-sm px-4 py-2' }
  const variants = {
    primary: 'bg-[var(--am)] text-[#0b0d12] hover:bg-[#f0b040] shadow-[0_0_16px_rgba(245,166,35,0.25)]',
    ghost:   'text-[var(--tx-2)] hover:text-[var(--tx-1)] hover:bg-[var(--bg-2)]',
    danger:  'bg-[var(--red-bg)] text-[var(--red)] border border-[var(--red-b)] hover:bg-[rgba(240,82,82,0.14)]',
    outline: 'border border-[var(--border-2)] text-[var(--tx-2)] hover:border-[var(--border-2)] hover:text-[var(--tx-1)] hover:bg-[var(--bg-2)]',
  }
  return (
    <button className={clsx(base, sizes[size], variants[variant], className)} disabled={loading} {...rest}>
      {loading ? <Loader2 size={13} className="animate-spin" /> : icon}
      {children}
    </button>
  )
}

// ── Card ────────────────────────────────────────────────────────
export function Card({ children, className, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('card', className)} {...rest}>{children}</div>
}

// ── Section header ─────────────────────────────────────────────
export function SectionHeader({ label, sub }: { label: string; sub?: string }) {
  return (
    <div className="mb-5">
      <h2 className="text-base font-semibold text-[var(--tx-1)]">{label}</h2>
      {sub && <p className="text-xs text-[var(--tx-3)] mt-0.5 font-mono">{sub}</p>}
    </div>
  )
}

// ── Stat card ───────────────────────────────────────────────────
interface StatCardProps {
  label: string
  value: string | number
  sub?: string
  accent?: string
  icon?: React.ReactNode
  delay?: number
}

export function StatCard({ label, value, sub, accent = 'var(--am)', icon, delay = 0 }: StatCardProps) {
  return (
    <Card
      className="p-5 fade-up flex flex-col gap-3"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono uppercase tracking-[0.1em] text-[var(--tx-3)]">{label}</span>
        {icon && <span className="text-[var(--tx-3)]">{icon}</span>}
      </div>
      <div className="font-display italic text-4xl" style={{ color: accent }}>
        {value}
      </div>
      {sub && <p className="text-xs text-[var(--tx-3)]">{sub}</p>}
    </Card>
  )
}

// ── Loading skeleton ────────────────────────────────────────────
export function Skeleton({ h = 'h-4', w = 'w-full' }: { h?: string; w?: string }) {
  return <div className={clsx('shimmer rounded', h, w)} />
}

// ── Empty state ─────────────────────────────────────────────────
export function EmptyState({ icon, title, body }: { icon: React.ReactNode; title: string; body?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
      <div className="text-3xl opacity-30">{icon}</div>
      <p className="text-sm font-medium text-[var(--tx-2)]">{title}</p>
      {body && <p className="text-xs text-[var(--tx-3)] max-w-xs">{body}</p>}
    </div>
  )
}

// ── Metric row ──────────────────────────────────────────────────
export function MetricRow({ label, value, of: total, color = 'var(--am)' }: { label: string; value: number; of?: number; color?: string }) {
  const pct = total ? Math.min((value / total) * 100, 100) : 0
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-[var(--tx-3)] font-mono w-24 shrink-0 truncate">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-[var(--bg-3)] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs font-mono text-[var(--tx-2)] w-8 text-right">{value}</span>
    </div>
  )
}

// ── Mono value ──────────────────────────────────────────────────
export function Mono({ children, muted }: { children: React.ReactNode; muted?: boolean }) {
  return (
    <span className={clsx('font-mono text-xs', muted ? 'text-[var(--tx-3)]' : 'text-[var(--tx-2)]')}>
      {children}
    </span>
  )
}

// ── Divider ─────────────────────────────────────────────────────
export function Divider() {
  return <div className="border-t border-[var(--border)] my-4" />
}

// ── Toast (simple) ──────────────────────────────────────────────
export function Toast({ message, type }: { message: string; type: 'ok' | 'err' }) {
  return (
    <div className={clsx(
      'fixed bottom-5 right-5 z-50 px-4 py-3 rounded-lg text-sm font-medium border flex items-center gap-2 fade-up shadow-xl',
      type === 'ok' ? 'bg-[var(--grn-bg)] border-[var(--grn-b)] text-[var(--grn)]' : 'bg-[var(--red-bg)] border-[var(--red-b)] text-[var(--red)]'
    )}>
      <span>{type === 'ok' ? '✓' : '✕'}</span>
      {message}
    </div>
  )
}

// ── Score bar ────────────────────────────────────────────────────
export function ScoreBar({ score }: { score: number }) {
  const abs = Math.abs(score)
  const pct = Math.min(abs * 80, 100)
  const isAnomaly = score < -0.1
  const color = isAnomaly ? 'var(--red)' : 'var(--grn)'
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 rounded-full bg-[var(--bg-3)] overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <Mono muted>{score.toFixed(3)}</Mono>
    </div>
  )
}

// ── Confusion matrix cell ────────────────────────────────────────
export function ConfusionMatrix({ tp, fp, fn, tn }: { tp: number; fp: number; fn: number; tn: number }) {
  const Cell = ({ v, label, color }: { v: number; label: string; color: string }) => (
    <div className="flex flex-col items-center justify-center p-3 rounded-lg bg-[var(--bg-2)] border border-[var(--border)] gap-1">
      <span className="font-display italic text-2xl" style={{ color }}>{v}</span>
      <span className="text-[9px] font-mono text-[var(--tx-3)] uppercase tracking-widest">{label}</span>
    </div>
  )
  return (
    <div className="grid grid-cols-2 gap-2">
      <Cell v={tp} label="True Pos" color="var(--grn)" />
      <Cell v={fp} label="False Pos" color="var(--red)" />
      <Cell v={fn} label="False Neg" color="var(--orn)" />
      <Cell v={tn} label="True Neg" color="var(--blu)" />
    </div>
  )
}