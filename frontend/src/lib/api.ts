const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

async function req<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`)
  return res.json()
}

// ── Types ──────────────────────────────────────────────────────
export interface Log {
  userId: string
  action: string
  resource: string
  label?: string
  timestamp?: string
  verdict?: string
}

export interface Rule {
  userId: string
  action: string
  resourcePattern: string
  support?: number
  confidence?: number
  type?: string
}

export interface InferResult {
  coarse_rules: Rule[]
  refined_rules: Rule[]
  baseline_logs: number
  logs_processed: number
  rules_generated: number
}

export interface DashboardSummary {
  total: number
  over_granted: number
  normal: number
  detection_rate: number
  trend: { date: string; over_granted: number; normal: number }[]
  rules_active: number
}

export interface DashboardStats {
  by_user: Record<string, { allowed: number; over_granted: number }>
  by_action: Record<string, { allowed: number; over_granted: number }>
  total_logs: number
  total_rules: number
}

export interface Metrics {
  precision: number
  recall: number
  f1_score: number
  train_size: number
  test_size: number
  tp: number
  fp: number
  fn: number
  tn: number
}

export interface CrossValidation {
  mean: Metrics
  std: Metrics
  folds: number
  fold_results: Metrics[]
}

export interface MLConfig {
  id?: string
  name?: string
  userId?: string
  resource?: string
  action?: string
  risk?: string
  issue?: string
}

export interface MLResult {
  id?: string
  name?: string
  anomaly_score: number
  risk?: string
  issue?: string
  flagged: boolean
  statistical_anomaly: boolean
  baseline_deviation: boolean
}

export interface BaselineComparison {
  naive: { tp: number; fp: number; fn: number; tn: number; precision: number; recall: number; f1_score: number; rules_count: number; method: string }
  trie:  { tp: number; fp: number; fn: number; tn: number; precision: number; recall: number; f1_score: number; rules_count: number; method: string }
}

export interface AblationStudy {
  [variant: string]: {
    mean: Metrics
    std: Metrics
    rules_count: number
    description: string
  }
}

// ── API calls ─────────────────────────────────────────────────
export const api = {
  health: () => req<{ status: string }>('/api/health'),

  // Logs
  uploadLogs: (logs: Log[]) => req<{ message: string; count: number }>('/api/logs/upload', 'POST', { logs }),
  getLogs: () => req<{ logs: (Log & { verdict: string })[]; count: number }>('/api/logs'),

  // Baseline
  inferBaseline: () => req<InferResult>('/api/baseline/infer', 'POST'),
  getRules: () => req<{ rules: Rule[]; count: number }>('/api/baseline/rules'),

  // Evaluate
  evaluate: (payload: { userId: string; resource: string; action: string }) =>
    req<{ verdict: string; risk: string }>('/api/evaluate', 'POST', payload),
  getMetrics: () => req<Metrics>('/api/evaluate/metrics'),
  crossValidate: (folds = 5) => req<{ cross_validation: CrossValidation; note: string; total_logs: number }>(`/api/evaluate/cross-validate?folds=${folds}`),
  compareBaselines: () => req<{ comparison: BaselineComparison; note: string }>('/api/evaluate/compare-baselines'),
  ablationStudy: () => req<{ ablation_study: AblationStudy; note: string }>('/api/evaluate/ablation'),

  // Dashboard
  getDashboard: () => req<DashboardSummary>('/api/dashboard/summary'),
  getStats: () => req<DashboardStats>('/api/dashboard/stats'),

  // ML
  mlAnalyze: (configs: MLConfig[]) => req<{ results: MLResult[]; flagged: number; statistical_anomalies: number; baseline_deviations: number }>('/api/ml/analyze', 'POST', { configs }),
}