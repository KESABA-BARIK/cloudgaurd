'use client'
import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { AlertTriangle, CheckCircle2, ShieldCheck, Activity } from 'lucide-react'
import { api, DashboardSummary, DashboardStats } from '@/lib/api'
import { StatCard, Card, Skeleton, MetricRow, Tag, Mono, Divider } from '@/components/ui'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card px-3 py-2 text-xs font-mono shadow-xl">
      <p className="text-[var(--tx-3)] mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value}</p>
      ))}
    </div>
  )
}

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([api.getDashboard(), api.getStats()])
      .then(([s, st]) => { setSummary(s); setStats(st) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="grid grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="card p-5 flex flex-col gap-3">
          <Skeleton h="h-3" w="w-24" />
          <Skeleton h="h-10" w="w-16" />
          <Skeleton h="h-3" w="w-32" />
        </div>
      ))}
    </div>
  )

  if (!summary) return (
    <div className="flex flex-col items-center justify-center py-24 gap-4">
      <AlertTriangle size={32} className="text-[var(--am)] opacity-60" />
      <p className="text-sm text-[var(--tx-2)]">No data yet — upload logs and run baseline inference first.</p>
    </div>
  )

  const total = summary.total || 1
  const byUser = stats?.by_user ? Object.entries(stats.by_user) : []
  const byAction = stats?.by_action ? Object.entries(stats.by_action) : []

  return (
    <div className="flex flex-col gap-6 fade-up">

      {/* Stat row */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total Requests"
          value={summary.total}
          sub="All evaluated log entries"
          accent="var(--blu)"
          icon={<Activity size={14} />}
          delay={0}
        />
        <StatCard
          label="Over-Granted"
          value={summary.over_granted}
          sub="Anomalous accesses detected"
          accent="var(--red)"
          icon={<AlertTriangle size={14} />}
          delay={60}
        />
        <StatCard
          label="Detection Rate"
          value={`${summary.detection_rate.toFixed(1)}%`}
          sub="Over-grants / total"
          accent="var(--am)"
          icon={<ShieldCheck size={14} />}
          delay={120}
        />
        <StatCard
          label="Active Rules"
          value={summary.rules_active}
          sub="Inferred baseline rules"
          accent="var(--grn)"
          icon={<CheckCircle2 size={14} />}
          delay={180}
        />
      </div>

      {/* Trend chart */}
      <Card className="p-5" style={{ animationDelay: '240ms' }}>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-sm font-semibold text-[var(--tx-1)]">Access Trend</h3>
            <p className="text-xs text-[var(--tx-3)] font-mono mt-0.5">over-granted vs normal over time</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-[var(--red)]" />
              <Mono muted>over-granted</Mono>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-[var(--grn)]" />
              <Mono muted>normal</Mono>
            </div>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={180}>
          <AreaChart data={summary.trend} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
            <defs>
              <linearGradient id="gNormal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="var(--grn)" stopOpacity={0.2} />
                <stop offset="95%" stopColor="var(--grn)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gOG" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="var(--red)" stopOpacity={0.25} />
                <stop offset="95%" stopColor="var(--red)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="normal"       name="normal"       stroke="var(--grn)" strokeWidth={1.5} fill="url(#gNormal)" dot={false} />
            <Area type="monotone" dataKey="over_granted" name="over-granted" stroke="var(--red)" strokeWidth={1.5} fill="url(#gOG)"    dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      {/* By user / by action */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="p-5">
          <h3 className="text-sm font-semibold mb-4 text-[var(--tx-1)]">By User</h3>
          <div className="flex flex-col gap-3">
            {byUser.length === 0 ? (
              <p className="text-xs text-[var(--tx-3)] font-mono">No data</p>
            ) : byUser.map(([user, counts]) => (
              <div key={user} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <Mono>{user}</Mono>
                  <div className="flex items-center gap-1.5">
                    {counts.over_granted > 0 && <Tag label={`${counts.over_granted} og`} variant="red" />}
                    <Tag label={`${counts.allowed} ok`} variant="green" />
                  </div>
                </div>
                <MetricRow
                  label=""
                  value={counts.over_granted}
                  of={counts.over_granted + counts.allowed}
                  color="var(--red)"
                />
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="text-sm font-semibold mb-4 text-[var(--tx-1)]">By Action</h3>
          <div className="flex flex-col gap-3">
            {byAction.length === 0 ? (
              <p className="text-xs text-[var(--tx-3)] font-mono">No data</p>
            ) : byAction.map(([action, counts]) => (
              <div key={action} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <Tag label={action} variant="blue" />
                  <div className="flex items-center gap-2">
                    <Mono muted>{counts.over_granted + counts.allowed} total</Mono>
                  </div>
                </div>
                <MetricRow
                  label=""
                  value={counts.over_granted}
                  of={counts.over_granted + counts.allowed}
                  color="var(--am)"
                />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}