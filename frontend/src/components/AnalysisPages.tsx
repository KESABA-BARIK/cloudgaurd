'use client'
import { useState } from 'react'
import { BrainCircuit, Play, RefreshCw } from 'lucide-react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import { api, MLResult, Metrics, CrossValidation, BaselineComparison, AblationStudy, VariantResult } from '@/lib/api'
import { SAMPLE_ML_CONFIGS } from '@/lib/sampleData'
import { Card, Btn, Tag, Mono, EmptyState, ScoreBar, ConfusionMatrix, SectionHeader, StatCard } from '@/components/ui'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card px-3 py-2 text-xs font-mono shadow-xl">
      <p className="text-[var(--tx-3)] mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</p>
      ))}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  ML ANOMALY PAGE
// ═══════════════════════════════════════════════════════════════
export function MLPage() {
  const [loading, setLoading] = useState(false)
  const [res, setRes] = useState<{ results: MLResult[]; flagged: number; statistical_anomalies: number; baseline_deviations: number } | null>(null)

  const run = async () => {
    setLoading(true)
    try {
      const data = await api.mlAnalyze(SAMPLE_ML_CONFIGS)
      setRes(data)
    } catch {}
    finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col gap-6 fade-up">
      <div className="flex items-center justify-between">
        <SectionHeader label="ML Anomaly Detection" sub="Isolation Forest on resource access features" />
        <Btn variant="primary" icon={<Play size={13} />} loading={loading} onClick={run}>
          Run Analysis
        </Btn>
      </div>

      {res && (
        <>
          <div className="grid grid-cols-4 gap-3">
            <StatCard label="Total Analyzed"      value={res.results.length}        accent="var(--blu)" />
            <StatCard label="Flagged"             value={res.flagged}               accent="var(--red)" />
            <StatCard label="Statistical Anom."   value={res.statistical_anomalies} accent="var(--orn)" />
            <StatCard label="Baseline Deviations" value={res.baseline_deviations}   accent="var(--am)"  />
          </div>

          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    {['Name', 'Anomaly Score', 'Risk', 'Issue', 'Statistical', 'Baseline Dev.', 'Flagged'].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-[10px] font-mono text-[var(--tx-3)] uppercase tracking-widest whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {res.results.map((r, i) => (
                    <tr key={i} className="border-b border-[var(--border)] border-opacity-40 hover:bg-[var(--bg-2)] transition-colors">
                      <td className="px-5 py-3"><Mono>{r.name ?? r.id ?? '—'}</Mono></td>
                      <td className="px-5 py-3"><ScoreBar score={r.anomaly_score} /></td>
                      <td className="px-5 py-3">{r.risk ? <Tag label={r.risk} /> : <Mono muted>—</Mono>}</td>
                      <td className="px-5 py-3 max-w-[200px] truncate"><Mono muted>{r.issue ?? '—'}</Mono></td>
                      <td className="px-5 py-3"><Tag label={r.statistical_anomaly ? 'YES' : 'NO'} variant={r.statistical_anomaly ? 'red' : 'green'} /></td>
                      <td className="px-5 py-3"><Tag label={r.baseline_deviation ? 'YES' : 'NO'} variant={r.baseline_deviation ? 'amber' : 'green'} /></td>
                      <td className="px-5 py-3"><Tag label={r.flagged ? 'FLAGGED' : 'CLEAN'} variant={r.flagged ? 'red' : 'green'} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {!res && !loading && (
        <EmptyState icon={<BrainCircuit size={36} />} title="Run ML Analysis" body="Isolation Forest will score each config for anomalous behavior." />
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  METRICS PAGE
// ═══════════════════════════════════════════════════════════════
function MetricBar({ label, value, color = 'var(--am)' }: { label: string; value: number; color?: string }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <Mono muted>{label}</Mono>
        <span className="font-display italic text-xl" style={{ color }}>{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--bg-3)] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${value * 100}%`, background: color }} />
      </div>
    </div>
  )
}

export function MetricsPage() {
  const [loading, setLoading] = useState(false)
  const [loadingCV, setLoadingCV] = useState(false)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [cv, setCV] = useState<CrossValidation | null>(null)

  const loadMetrics = async () => {
    setLoading(true)
    try { setMetrics(await api.getMetrics()) } catch {}
    finally { setLoading(false) }
  }

  const loadCV = async () => {
    setLoadingCV(true)
    try { const r = await api.crossValidate(5); setCV(r.cross_validation) } catch {}
    finally { setLoadingCV(false) }
  }

  const radarData = metrics ? [
    { metric: 'Precision', value: metrics.precision },
    { metric: 'Recall',    value: metrics.recall },
    { metric: 'F1 Score',  value: metrics.f1_score },
    { metric: 'TP Rate',   value: (metrics.tp / Math.max(metrics.tp + metrics.fn, 1)) },
    { metric: 'TN Rate',   value: (metrics.tn / Math.max(metrics.tn + metrics.fp, 1)) },
  ] : []

  return (
    <div className="flex flex-col gap-6 fade-up">
      <div className="flex items-center gap-3 flex-wrap">
        <SectionHeader label="Evaluation Metrics" sub="Train/test split and 5-fold cross-validation" />
        <Btn variant="outline" icon={<Play size={13} />} loading={loading} onClick={loadMetrics} size="sm">
          Compute Metrics
        </Btn>
        <Btn variant="outline" icon={<RefreshCw size={13} />} loading={loadingCV} onClick={loadCV} size="sm">
          5-Fold CV
        </Btn>
      </div>

      {metrics && (
        <div className="grid grid-cols-2 gap-5">
          <Card className="p-5 flex flex-col gap-5">
            <p className="text-sm font-semibold">Performance Metrics</p>
            <MetricBar label="Precision" value={metrics.precision} color="var(--am)" />
            <MetricBar label="Recall"    value={metrics.recall}    color="var(--blu)" />
            <MetricBar label="F1 Score"  value={metrics.f1_score}  color="var(--grn)" />
            <div className="flex items-center gap-4 pt-2 border-t border-[var(--border)]">
              <div><Mono muted>Train size</Mono><br/><span className="font-display italic text-lg text-[var(--tx-1)]">{metrics.train_size}</span></div>
              <div><Mono muted>Test size</Mono><br/><span className="font-display italic text-lg text-[var(--tx-1)]">{metrics.test_size}</span></div>
            </div>
          </Card>

          <Card className="p-5">
            <p className="text-sm font-semibold mb-4">Confusion Matrix</p>
            <ConfusionMatrix tp={metrics.tp} fp={metrics.fp} fn={metrics.fn} tn={metrics.tn} />

            {radarData.length > 0 && (
              <div className="mt-4">
                <ResponsiveContainer width="100%" height={160}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="var(--border)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} />
                    <Radar name="score" dataKey="value" stroke="var(--am)" fill="var(--am)" fillOpacity={0.15} strokeWidth={1.5} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </div>
      )}

      {cv && (
        <Card className="p-5">
          <p className="text-sm font-semibold mb-4">5-Fold Cross-Validation — Mean ± Std</p>
          <div className="grid grid-cols-3 gap-4 mb-5">
            {[
              { k: 'Precision', v: cv.mean.precision, s: cv.std.precision, c: 'var(--am)' },
              { k: 'Recall',    v: cv.mean.recall,    s: cv.std.recall,    c: 'var(--blu)' },
              { k: 'F1 Score',  v: cv.mean.f1_score,  s: cv.std.f1_score,  c: 'var(--grn)' },
            ].map(m => (
              <div key={m.k} className="flex flex-col gap-1 p-3 rounded-lg bg-[var(--bg-2)] border border-[var(--border)]">
                <Mono muted>{m.k}</Mono>
                <span className="font-display italic text-2xl" style={{ color: m.c }}>{(m.v * 100).toFixed(1)}%</span>
                <Mono muted>± {(m.s * 100).toFixed(1)}%</Mono>
              </div>
            ))}
          </div>

          {cv.fold_results && (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={cv.fold_results.map((f, i) => ({ fold: `F${i+1}`, precision: f.precision, recall: f.recall, f1: f.f1_score }))}>
                <XAxis dataKey="fold" tick={{ fontSize: 10, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 10, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="precision" name="Precision" fill="var(--am)"  radius={[3,3,0,0]} />
                <Bar dataKey="recall"    name="Recall"    fill="var(--blu)" radius={[3,3,0,0]} />
                <Bar dataKey="f1"        name="F1"        fill="var(--grn)" radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      )}

      {!metrics && !cv && !loading && !loadingCV && (
        <EmptyState icon="📊" title="No metrics yet" body="Upload logs, run baseline, then compute metrics." />
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  COMPARE BASELINES PAGE
// ═══════════════════════════════════════════════════════════════
export function ComparePage() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<BaselineComparison | null>(null)

  const load = async () => {
    setLoading(true)
    try { const r = await api.compareBaselines(); setData(r.comparison) } catch {}
    finally { setLoading(false) }
  }

  const chartData = data ? [
    { metric: 'Precision', Naive: data.naive.precision, Trie: data.trie.precision },
    { metric: 'Recall',    Naive: data.naive.recall,    Trie: data.trie.recall    },
    { metric: 'F1 Score',  Naive: data.naive.f1_score,  Trie: data.trie.f1_score  },
  ] : []

  return (
    <div className="flex flex-col gap-6 fade-up">
      <div className="flex items-center justify-between">
        <SectionHeader label="Baseline Comparison" sub="Naive frequency-based vs Trie pattern-based method" />
        <Btn variant="primary" icon={<Play size={13} />} loading={loading} onClick={load}>
          Compare
        </Btn>
      </div>

      {data && (
        <>
          <div className="grid grid-cols-2 gap-5">
            {[
              { label: 'Naive (Top-K Frequency)', d: data.naive, color: 'var(--blu)' },
              { label: 'Trie (Pattern Mining)',   d: data.trie,  color: 'var(--am)' },
            ].map(({ label, d, color }) => (
              <Card key={label} className="p-5 flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold" style={{ color }}>{label}</p>
                  <Mono muted>{d.rules_count} rules</Mono>
                </div>
                <div className="flex flex-col gap-3">
                  {[
                    { k: 'Precision', v: d.precision },
                    { k: 'Recall',    v: d.recall    },
                    { k: 'F1 Score',  v: d.f1_score  },
                  ].map(m => (
                    <div key={m.k} className="flex flex-col gap-1.5">
                      <div className="flex justify-between">
                        <Mono muted>{m.k}</Mono>
                        <span className="font-mono text-xs" style={{ color }}>{(m.v * 100).toFixed(1)}%</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-[var(--bg-3)] overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${m.v * 100}%`, background: color }} />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="pt-2 border-t border-[var(--border)] grid grid-cols-4 gap-2">
                  {[['TP', d.tp, 'var(--grn)'], ['FP', d.fp, 'var(--red)'], ['FN', d.fn, 'var(--orn)'], ['TN', d.tn, 'var(--blu)']].map(([k, v, c]) => (
                    <div key={k as string} className="text-center">
                      <p className="font-display italic text-xl" style={{ color: c as string }}>{v as number}</p>
                      <Mono muted>{k}</Mono>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>

          <Card className="p-5">
            <p className="text-sm font-semibold mb-4">Side-by-Side Comparison</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} barCategoryGap="30%">
                <XAxis dataKey="metric" tick={{ fontSize: 11, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 10, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="Naive" fill="var(--blu)" radius={[4,4,0,0]} />
                <Bar dataKey="Trie"  fill="var(--am)"  radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}

      {!data && !loading && (
        <EmptyState icon="⚖️" title="No comparison data" body="Upload labeled logs and run baseline first." />
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  ABLATION STUDY PAGE
// ═══════════════════════════════════════════════════════════════
export function AblationPage() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<AblationStudy | null>(null)

  const run = async () => {
    setLoading(true)
    try { const r = await api.ablationStudy(); setData(r.ablation_study) } catch {}
    finally { setLoading(false) }
  }

  // Parse variants from nested results structure: data.results contains "current", "loose", "prefix" variants
  const variants = data && data.results ? Object.entries(data.results as Record<string, VariantResult>) : []
  const colors = ['var(--am)', 'var(--blu)', 'var(--grn)', 'var(--orn)', 'var(--red)']

  const chartData = variants.length ? ['precision', 'recall', 'f1_score'].map(metric => ({
    metric: metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    ...Object.fromEntries(variants.map(([name, v]) => [name, (v as VariantResult)?.mean?.[metric as keyof Metrics] ?? 0]))
  })) : []

  return (
    <div className="flex flex-col gap-6 fade-up">
      <div className="flex items-center justify-between">
        <SectionHeader label="Ablation Study" sub="Compare impact of design choices on detection performance" />
        <Btn variant="primary" icon={<Play size={13} />} loading={loading} onClick={run}>
          Run Study
        </Btn>
      </div>

      {variants.length > 0 && (
        <>
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${Math.min(variants.length, 3)}, 1fr)` }}>
            {variants.map(([name, v], i) => {
              const variant = v as VariantResult
              return (
              <Card key={name} className="p-5 flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-6 rounded-full" style={{ background: colors[i] }} />
                  <p className="text-sm font-semibold text-[var(--tx-1)]">{name}</p>
                </div>
                {variant.description && <p className="text-xs text-[var(--tx-3)] leading-relaxed">{variant.description}</p>}
                <div className="flex flex-col gap-2 pt-2">
                  {[
                    { k: 'Precision', val: variant?.mean?.precision, std: variant?.std?.precision },
                    { k: 'Recall',    val: variant?.mean?.recall,    std: variant?.std?.recall    },
                    { k: 'F1',        val: variant?.mean?.f1_score,  std: variant?.std?.f1_score  },
                  ].map(m => (
                    <div key={m.k} className="flex items-center justify-between">
                      <Mono muted>{m.k}</Mono>
                      <div className="text-right">
                        <span className="font-mono text-xs" style={{ color: colors[i] }}>{(m.val ? m.val * 100 : 0).toFixed(1)}%</span>
                        {m.std !== undefined && <span className="font-mono text-[10px] text-[var(--tx-3)] ml-1">±{(m.std * 100).toFixed(1)}</span>}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="pt-2 border-t border-[var(--border)]">
                  <Mono muted>Rules: {variant.rules_count ?? '—'}</Mono>
                </div>
              </Card>
            )
            })}
          </div>

          {chartData.length > 0 && (
            <Card className="p-5">
              <p className="text-sm font-semibold mb-4">Metric Comparison Across Variants</p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} barCategoryGap="25%">
                  <XAxis dataKey="metric" tick={{ fontSize: 11, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 1]} tick={{ fontSize: 10, fontFamily: 'var(--font-mono)', fill: 'var(--tx-3)' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  {variants.map(([name], i) => (
                    <Bar key={name} dataKey={name} fill={colors[i]} radius={[3,3,0,0]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </>
      )}

      {!variants.length && !loading && (
        <EmptyState icon="🧪" title="No ablation data" body="Upload labeled logs, run baseline, then click Run Study." />
      )}
    </div>
  )
}