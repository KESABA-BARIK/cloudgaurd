'use client'

import { Suspense, useState } from 'react'
import { Sidebar, Page } from '@/components/Sidebar'
import { DashboardPage } from '@/components/DashboardPage'
import { UploadPage, BaselinePage, EvaluatePage, LogsPage } from '@/components/DataPages'
import { MLPage, MetricsPage, ComparePage, AblationPage } from '@/components/AnalysisPages'

const PAGE_LABELS: Record<Page, string> = {
  dashboard: 'Dashboard',
  upload:    'Upload Logs',
  baseline:  'Baseline Inference',
  evaluate:  'Live Evaluate',
  ml:        'ML Anomaly Detection',
  logs:      'Access Logs',
  metrics:   'Evaluation Metrics',
  compare:   'Compare Baselines',
  ablation:  'Ablation Study',
}

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')

  const renderPage = () => {
    switch (page) {
      case 'dashboard': return <DashboardPage />
      case 'upload':    return <UploadPage />
      case 'baseline':  return <BaselinePage />
      case 'evaluate':  return <EvaluatePage />
      case 'ml':        return <MLPage />
      case 'logs':      return <LogsPage />
      case 'metrics':   return <MetricsPage />
      case 'compare':   return <ComparePage />
      case 'ablation':  return <AblationPage />
    }
  }

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg)' }}>
      <Sidebar current={page} onChange={setPage} />

      {/* Main content area */}
      <main className="ml-[210px] min-h-screen flex flex-col">

        {/* Topbar */}
        <header
          className="sticky top-0 z-30 flex items-center justify-between px-8 py-4 border-b border-[var(--border)]"
          style={{ background: 'rgba(11,13,18,0.85)', backdropFilter: 'blur(12px)' }}
        >
          <div>
            <h1 className="text-sm font-semibold text-[var(--tx-1)]">{PAGE_LABELS[page]}</h1>
            <p className="text-[10px] font-mono text-[var(--tx-3)] mt-0.5">
              CloudGuard · AI-Powered Cloud Misconfiguration Detection
            </p>
          </div>

          {/* Breadcrumb */}
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--tx-3)]">
            <span>cloudguard</span>
            <span>/</span>
            <span className="text-[var(--am)]">{page}</span>
          </div>
        </header>

        {/* Page content */}
        <Suspense fallback={<div>Loading...</div>}>
            {renderPage()}
        </Suspense>

        {/* Footer */}
        <footer className="px-8 py-4 border-t border-[var(--border)] flex items-center justify-between">
          <p className="text-[10px] font-mono text-[var(--tx-3)]">
            CloudGuard — Extended from OPMonitor (Wang et al., 2025, Computers &amp; Security)
          </p>
          <p className="text-[10px] font-mono text-[var(--tx-3)]">
            Backend: <span className="text-[var(--grn)]">localhost:5000</span>
          </p>
        </footer>
      </main>
    </div>
  )
}