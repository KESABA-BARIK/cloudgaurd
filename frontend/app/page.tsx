'use client'

import { Suspense, useState, useEffect } from 'react'
import { Sidebar, Page } from '@/components/Sidebar'
import { DashboardPage } from '@/components/DashboardPage'
import { ConfigUploadPage } from '@/components/ConfigPage'
import { RiskAnalysisPage } from '@/components/RiskAnalysisPage'
import { UploadPage, BaselinePage, EvaluatePage, LogsPage } from '@/components/DataPages'
import { MLPage, MetricsPage, ComparePage, AblationPage } from '@/components/AnalysisPages'
import { Download } from 'lucide-react'

const PAGE_LABELS: Record<Page, string> = {
  dashboard: 'Dashboard',
  config:    'Upload Configuration',
  risk:      'Risk Analysis & Remediation',
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
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')

  // Load theme preference from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'dark' | 'light'
    if (savedTheme) setTheme(savedTheme)
  }, [])

  // Save theme preference
  const handleThemeChange = (newTheme: 'dark' | 'light') => {
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    // Apply theme to document if needed
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  const renderPage = () => {
    switch (page) {
      case 'dashboard': return <DashboardPage />
      case 'config':    return <ConfigUploadPage />
      case 'risk':      return <RiskAnalysisPage />
      case 'baseline':  return <BaselinePage />
      case 'evaluate':  return <EvaluatePage />
      case 'ml':        return <MLPage />
      case 'logs':      return <LogsPage />
      case 'metrics':   return <MetricsPage />
      case 'compare':   return <ComparePage />
      case 'ablation':  return <AblationPage />
    }
  }

  const handleExport = async () => {
    try {
      let exportData: any = {
        title: `CloudGuard ${PAGE_LABELS[page]} Report`,
        timestamp: new Date().toISOString(),
        page: page,
        theme: theme,
        note: 'Export from CloudGuard AI Security Analysis System. Extended from OPMonitor (Wang et al., 2025)'
      }

      // Fetch page-specific data from backend
      if (page === 'config') {
        const res = await fetch('http://localhost:5000/api/config/export/summary')
        if (res.ok) {
          const data = await res.json()
          exportData.data = data
        }
      } else if (page === 'baseline') {
        const res = await fetch('http://localhost:5000/api/baseline/infer')
        if (res.ok) {
          const data = await res.json()
          exportData.data = data
        }
      } else if (page === 'evaluate') {
        const res = await fetch('http://localhost:5000/api/evaluate/metrics')
        if (res.ok) {
          const data = await res.json()
          exportData.data = data
        }
      } else if (page === 'ablation') {
        const res = await fetch('http://localhost:5000/api/ablation/study')
        if (res.ok) {
          const data = await res.json()
          exportData.data = data
        }
      }

      const dataStr = JSON.stringify(exportData, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `cloudguard-${page}-report-${Date.now()}.json`
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg)' }}>
      <Sidebar current={page} onChange={setPage} theme={theme} onThemeChange={handleThemeChange} />

      {/* Main content area */}
      <main className="ml-[210px] min-h-screen flex flex-col flex-1">

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

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleExport}
              className="px-3 py-2 text-xs font-medium rounded bg-[var(--am)]/10 hover:bg-[var(--am)]/20 text-[var(--am)] flex items-center gap-2 transition"
            >
              <Download size={14} /> Export
            </button>

            {/* Breadcrumb */}
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--tx-3)]">
              <span>cloudguard</span>
              <span>/</span>
              <span className="text-[var(--am)]">{page}</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <Suspense fallback={
          <div className="flex items-center justify-center flex-1">
            <div className="text-[var(--tx-3)]">Loading...</div>
          </div>
        }>
          {renderPage()}
        </Suspense>

        {/* Footer */}
        <footer className="px-8 py-4 border-t border-[var(--border)] flex items-center justify-between mt-auto">
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