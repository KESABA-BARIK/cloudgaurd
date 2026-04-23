'use client'
import { useState, useCallback } from 'react'
import { UploadCloud, Play, RefreshCw, CheckCircle2, XCircle, AlertTriangle, Copy } from 'lucide-react'
import { api, Log, Rule, InferResult } from '@/lib/api'
import { SAMPLE_LOGS } from '@/lib/sampleData'
import { Card, Btn, Tag, VerdictTag, Mono, EmptyState, Skeleton, SectionHeader, Toast, Divider } from '@/components/ui'
import { clsx } from 'clsx'

// ═══════════════════════════════════════════════════════════════
//  UPLOAD PAGE
// ═══════════════════════════════════════════════════════════════
export function UploadPage() {
  const [raw, setRaw] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ message: string; count: number } | null>(null)
  const [err, setErr] = useState('')

  const loadSample = () => {
    setRaw(JSON.stringify(SAMPLE_LOGS, null, 2))
    setErr('')
    setResult(null)
  }

  const handleUpload = async () => {
    setErr('')
    setResult(null)
    let logs: Log[]
    try { logs = JSON.parse(raw) } catch { setErr('Invalid JSON — check your format.'); return }
    if (!Array.isArray(logs)) { setErr('Logs must be a JSON array.'); return }
    setLoading(true)
    try {
      const res = await api.uploadLogs(logs)
      setResult(res)
    } catch (e: any) {
      setErr(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-3xl fade-up">
      <SectionHeader label="Upload Access Logs" sub="JSON array of log entries — see schema below" />

      {/* Schema hint */}
      <Card className="p-4">
        <p className="text-[10px] font-mono text-[var(--tx-3)] mb-2 tracking-widest uppercase">Required fields per entry</p>
        <pre className="text-xs font-mono text-[var(--tx-2)] leading-relaxed">{`{
  "userId":    "string",   // who is accessing
  "action":    "string",   // READ | WRITE | DELETE | ...
  "resource":  "string",   // e.g. s3://bucket/path/file.txt
  "label":     "string",   // "allowed" | "over-granted"  (optional, needed for metrics)
  "timestamp": "string"    // ISO 8601  (optional)
}`}</pre>
      </Card>

      {/* Textarea */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-mono text-[var(--tx-3)]">Paste JSON here</p>
          <Btn size="sm" variant="ghost" icon={<Copy size={11} />} onClick={loadSample}>
            Load sample data ({SAMPLE_LOGS.length} entries)
          </Btn>
        </div>
        <textarea
          className="w-full h-64 p-4 rounded-lg bg-[var(--bg-2)] border border-[var(--border)] font-mono text-xs text-[var(--tx-1)] resize-none focus:outline-none focus:border-[var(--am)] transition-colors"
          placeholder='[{ "userId": "alice", "action": "READ", "resource": "s3://..." }]'
          value={raw}
          onChange={e => setRaw(e.target.value)}
        />
      </div>

      {err && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-[var(--red-bg)] border border-[var(--red-b)] text-[var(--red)] text-sm">
          <XCircle size={14} /> {err}
        </div>
      )}

      {result && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-[var(--grn-bg)] border border-[var(--grn-b)] text-[var(--grn)] text-sm">
          <CheckCircle2 size={14} /> {result.message} — <strong>{result.count}</strong> logs uploaded
        </div>
      )}

      <Btn variant="primary" loading={loading} icon={<UploadCloud size={14} />} onClick={handleUpload}>
        Upload Logs
      </Btn>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  BASELINE PAGE
// ═══════════════════════════════════════════════════════════════
export function BaselinePage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<InferResult | null>(null)
  const [err, setErr] = useState('')

  const run = async () => {
    setErr('')
    setLoading(true)
    try {
      const res = await api.inferBaseline()
      setResult(res)
    } catch (e: any) {
      setErr(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6 fade-up">
      <div className="flex items-center justify-between">
        <SectionHeader label="Baseline Inference" sub="Two-phase Trie-based rule mining (OPMonitor algorithm)" />
        <Btn variant="primary" loading={loading} icon={<Play size={13} />} onClick={run}>
          Run Inference
        </Btn>
      </div>

      {/* Phase explanation */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { num: '01', title: 'Coarse Mining', desc: 'Group logs by (userId, action), build Trie of resource paths, extract maximal patterns.' },
          { num: '02', title: 'Rule Refinement', desc: 'Clean up patterns, preserve :// separators, remove duplicated slashes.' },
          { num: '03', title: 'Baseline Ready', desc: 'Refined rules stored in DB. Used for real-time evaluation of incoming requests.' },
        ].map((p, i) => (
          <Card key={i} className="p-4">
            <p className="text-[10px] font-mono text-[var(--tx-3)] mb-2">PHASE {p.num}</p>
            <p className="text-sm font-semibold text-[var(--am)] mb-1">{p.title}</p>
            <p className="text-xs text-[var(--tx-3)] leading-relaxed">{p.desc}</p>
          </Card>
        ))}
      </div>

      {err && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-[var(--red-bg)] border border-[var(--red-b)] text-[var(--red)] text-sm">
          <XCircle size={14} /> {err}
        </div>
      )}

      {loading && (
        <div className="flex flex-col gap-3">
          {[...Array(4)].map((_, i) => <Skeleton key={i} h="h-14" />)}
        </div>
      )}

      {result && !loading && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Logs Processed', value: result.logs_processed },
              { label: 'Coarse Rules',   value: result.coarse_rules?.length ?? 0 },
              { label: 'Refined Rules',  value: result.refined_rules?.length ?? result.rules_generated },
            ].map((s, i) => (
              <Card key={i} className="p-4 flex flex-col gap-2">
                <p className="text-[10px] font-mono text-[var(--tx-3)] uppercase tracking-widest">{s.label}</p>
                <p className="font-display italic text-3xl text-[var(--am)]">{s.value}</p>
              </Card>
            ))}
          </div>

          {/* Rules table */}
          <Card>
            <div className="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
              <p className="text-sm font-semibold">Refined Rules</p>
              <Tag label={`${result.refined_rules?.length ?? 0} rules`} variant="amber" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    {['User', 'Action', 'Resource Pattern', 'Support', 'Type'].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-[10px] font-mono text-[var(--tx-3)] uppercase tracking-widest">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(result.refined_rules ?? []).map((r, i) => (
                    <tr key={i} className="border-b border-[var(--border)] border-opacity-50 hover:bg-[var(--bg-2)] transition-colors">
                      <td className="px-5 py-3"><Mono>{r.userId}</Mono></td>
                      <td className="px-5 py-3"><Tag label={r.action} variant="blue" /></td>
                      <td className="px-5 py-3 max-w-xs truncate"><Mono muted>{r.resourcePattern}</Mono></td>
                      <td className="px-5 py-3"><Mono muted>{r.support ?? '—'}</Mono></td>
                      <td className="px-5 py-3"><Tag label={r.type ?? 'refined'} variant="muted" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {!result && !loading && (
        <EmptyState icon="🔍" title="No baseline yet" body="Click Run Inference to mine rules from your uploaded logs." />
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  LIVE EVALUATE PAGE
// ═══════════════════════════════════════════════════════════════
interface EvalEntry { userId: string; resource: string; action: string; verdict: string; risk: string; ts: string }

const QUICK_TESTS = [
  { label: 'Alice → reports (✓)', userId: 'alice', action: 'READ',   resource: 's3://corp-data/reports/q1-2026.pdf', expect: 'allowed' },
  { label: 'Alice → secrets (✗)', userId: 'alice', action: 'READ',   resource: 's3://corp-data/secrets/api-keys.json', expect: 'over-granted' },
  { label: 'Bob   → ec2 (✓)',    userId: 'bob',   action: 'WRITE',  resource: 'ec2://instances/i-0a1b2c3d/config', expect: 'allowed' },
  { label: 'Dave  → schema (✗)', userId: 'dave',  action: 'WRITE',  resource: 'db://prod/schema/users', expect: 'over-granted' },
]

export function EvaluatePage() {
  const [form, setForm] = useState({ userId: 'alice', resource: 's3://corp-data/reports/q1-2026.pdf', action: 'READ' })
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<EvalEntry[]>([])
  const [err, setErr] = useState('')

  const evaluate = useCallback(async (override?: typeof form) => {
    const payload = override ?? form
    if (!payload.userId || !payload.resource || !payload.action) return
    setLoading(true)
    setErr('')
    try {
      const res = await api.evaluate(payload)
      setHistory(prev => [{
        ...payload, verdict: res.verdict, risk: res.risk, ts: new Date().toLocaleTimeString()
      }, ...prev].slice(0, 30))
    } catch (e: any) {
      setErr(e.message)
    } finally {
      setLoading(false)
    }
  }, [form])

  const latest = history[0]

  return (
    <div className="flex flex-col gap-6 fade-up">
      <SectionHeader label="Live Evaluate" sub="Test an access request against the inferred baseline" />

      <div className="grid grid-cols-2 gap-5">
        {/* Form */}
        <Card className="p-5 flex flex-col gap-4">
          {['userId', 'resource', 'action'].map(key => (
            <div key={key} className="flex flex-col gap-1.5">
              <label className="text-[10px] font-mono text-[var(--tx-3)] uppercase tracking-widest">{key}</label>
              <input
                value={(form as any)[key]}
                onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                className="bg-[var(--bg-2)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm font-mono text-[var(--tx-1)] focus:outline-none focus:border-[var(--am)] transition-colors"
              />
            </div>
          ))}

          {err && <p className="text-xs text-[var(--red)] font-mono">{err}</p>}

          <Btn variant="primary" loading={loading} icon={<Play size={13} />} onClick={() => evaluate()}>
            Evaluate Request
          </Btn>

          {/* Latest result */}
          {latest && (
            <div className={clsx(
              'mt-2 p-4 rounded-lg border flex flex-col gap-2',
              latest.verdict === 'over-granted'
                ? 'bg-[var(--red-bg)] border-[var(--red-b)]'
                : 'bg-[var(--grn-bg)] border-[var(--grn-b)]'
            )}>
              <div className="flex items-center gap-2">
                {latest.verdict === 'over-granted'
                  ? <XCircle size={14} className="text-[var(--red)]" />
                  : <CheckCircle2 size={14} className="text-[var(--grn)]" />}
                <span className="font-display italic text-lg" style={{ color: latest.verdict === 'over-granted' ? 'var(--red)' : 'var(--grn)' }}>
                  {latest.verdict.replace('-', ' ')}
                </span>
                <span className="ml-auto text-[9px] font-mono text-[var(--tx-3)]">{latest.ts}</span>
              </div>
              <Mono muted>{latest.resource}</Mono>
            </div>
          )}
        </Card>

        {/* Quick tests */}
        <div className="flex flex-col gap-3">
          <p className="text-xs font-mono text-[var(--tx-3)] uppercase tracking-widest">Quick Tests</p>
          {QUICK_TESTS.map((t, i) => (
            <button
              key={i}
              onClick={() => { setForm({ userId: t.userId, resource: t.resource, action: t.action }); evaluate({ userId: t.userId, resource: t.resource, action: t.action }) }}
              className="flex items-center justify-between px-4 py-3 rounded-lg bg-[var(--bg-2)] border border-[var(--border)] hover:border-[var(--am)] text-left transition-all group"
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-xs font-medium text-[var(--tx-1)] group-hover:text-[var(--am)] transition-colors">{t.label}</span>
                <Mono muted>{t.resource.split('/').slice(-1)[0]}</Mono>
              </div>
              <Tag label={t.expect} variant={t.expect === 'allowed' ? 'green' : 'red'} />
            </button>
          ))}
        </div>
      </div>

      {/* History */}
      {history.length > 0 && (
        <Card>
          <div className="px-5 py-4 border-b border-[var(--border)]">
            <p className="text-sm font-semibold">Evaluation History</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {['Time', 'User', 'Action', 'Resource', 'Verdict'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-[10px] font-mono text-[var(--tx-3)] uppercase tracking-widest">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map((e, i) => (
                  <tr key={i} className="border-b border-[var(--border)] border-opacity-40 hover:bg-[var(--bg-2)] transition-colors">
                    <td className="px-5 py-2.5"><Mono muted>{e.ts}</Mono></td>
                    <td className="px-5 py-2.5"><Mono>{e.userId}</Mono></td>
                    <td className="px-5 py-2.5"><Tag label={e.action} variant="blue" /></td>
                    <td className="px-5 py-2.5 max-w-xs truncate"><Mono muted>{e.resource}</Mono></td>
                    <td className="px-5 py-2.5"><VerdictTag verdict={e.verdict} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  LOGS PAGE
// ═══════════════════════════════════════════════════════════════
export function LogsPage() {
  const [logs, setLogs] = useState<(Log & { verdict: string })[]>([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState<'all' | 'over-granted' | 'allowed'>('all')

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.getLogs()
      setLogs(res.logs)
    } catch {}
    finally { setLoading(false) }
  }

  const filtered = filter === 'all' ? logs : logs.filter(l => l.verdict === filter)
  const ogCount = logs.filter(l => l.verdict === 'over-granted').length

  return (
    <div className="flex flex-col gap-6 fade-up">
      <div className="flex items-center justify-between">
        <SectionHeader label="Access Logs" sub="All log entries with OPMonitor verdict" />
        <Btn variant="primary" icon={<RefreshCw size={13} />} loading={loading} onClick={load}>
          Load Logs
        </Btn>
      </div>

      {logs.length > 0 && (
        <div className="flex items-center gap-2">
          {(['all', 'allowed', 'over-granted'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={clsx(
                'px-3 py-1.5 rounded-md text-xs font-medium border transition-all',
                filter === f
                  ? 'bg-[var(--am-bg)] border-[var(--am-border)] text-[var(--am)]'
                  : 'border-[var(--border)] text-[var(--tx-3)] hover:text-[var(--tx-1)] hover:bg-[var(--bg-2)]'
              )}
            >
              {f === 'all' ? `All (${logs.length})` : f === 'over-granted' ? `Over-granted (${ogCount})` : `Allowed (${logs.length - ogCount})`}
            </button>
          ))}
        </div>
      )}

      {loading && <div className="flex flex-col gap-2">{[...Array(6)].map((_, i) => <Skeleton key={i} h="h-11" />)}</div>}

      {!loading && filtered.length === 0 && (
        <EmptyState icon="📋" title="No logs" body="Click Load Logs, or upload data first." />
      )}

      {!loading && filtered.length > 0 && (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {['Timestamp', 'User', 'Action', 'Resource', 'Label', 'Verdict'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-[10px] font-mono text-[var(--tx-3)] uppercase tracking-widest">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((l, i) => (
                  <tr
                    key={i}
                    className={clsx(
                      'border-b border-[var(--border)] border-opacity-40 hover:bg-[var(--bg-2)] transition-colors',
                      l.verdict === 'over-granted' && 'bg-[rgba(240,82,82,0.02)]'
                    )}
                  >
                    <td className="px-5 py-2.5"><Mono muted>{l.timestamp ? new Date(l.timestamp).toLocaleString() : '—'}</Mono></td>
                    <td className="px-5 py-2.5"><Mono>{l.userId}</Mono></td>
                    <td className="px-5 py-2.5"><Tag label={l.action} variant="blue" /></td>
                    <td className="px-5 py-2.5 max-w-xs truncate"><Mono muted>{l.resource}</Mono></td>
                    <td className="px-5 py-2.5">{l.label ? <Tag label={l.label} variant={l.label === 'allowed' ? 'green' : 'red'} /> : <Mono muted>—</Mono>}</td>
                    <td className="px-5 py-2.5"><VerdictTag verdict={l.verdict} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}