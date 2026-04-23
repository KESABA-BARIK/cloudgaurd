'use client'

import { Suspense, useState, useEffect } from 'react'
import { Sidebar, Page } from '@/components/Sidebar'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
import { DashboardPage } from '@/components/DashboardPage'
import { ConfigUploadPage } from '@/components/ConfigPage'
import { RiskAnalysisPage } from '@/components/RiskAnalysisPage'
import { UploadPage, BaselinePage, EvaluatePage, LogsPage } from '@/components/DataPages'
import { MLPage, MetricsPage, ComparePage, AblationPage } from '@/components/AnalysisPages'
import { Download, FileJson, BarChart3 } from 'lucide-react'

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
  const [showExportMenu, setShowExportMenu] = useState(false)

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('[class*="relative"]')) {
        setShowExportMenu(false)
      }
    }
    if (showExportMenu) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [showExportMenu])

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

  const handleExport = async (format: 'json' | 'csv' = 'json') => {
    try {
      setShowExportMenu(false)
      
      let fileContent = ''
      let fileName = `cloudguard-${page}-report-${Date.now()}`
      let mimeType = format === 'csv' ? 'text/csv' : 'application/json'

      // Fetch page-specific data from backend
      if (page === 'config') {
        const res = await fetch(`${API_BASE}/api/config/export/summary`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ format, include_details: true })
        })
        if (res.ok) {
          fileContent = await res.text()
          fileName += format === 'csv' ? '.csv' : '.json'
        }
      } else if (page === 'baseline') {
        const res = await fetch(`${API_BASE}/api/baseline/infer`, { method: 'POST' })
        if (res.ok) {
          const data = await res.json()
          fileContent = format === 'json' 
            ? JSON.stringify({ title: PAGE_LABELS[page], timestamp: new Date().toISOString(), data }, null, 2)
            : convertJsonToCsv(data, 'baseline')
          fileName += format === 'csv' ? '.csv' : '.json'
        }
      } else if (page === 'evaluate') {
        const res = await fetch(`${API_BASE}/api/evaluate/metrics`)
        if (res.ok) {
          const data = await res.json()
          fileContent = format === 'json'
            ? JSON.stringify({ title: PAGE_LABELS[page], timestamp: new Date().toISOString(), data }, null, 2)
            : convertJsonToCsv(data, 'metrics')
          fileName += format === 'csv' ? '.csv' : '.json'
        }
      } else if (page === 'ablation') {
        const res = await fetch(`${API_BASE}/api/evaluate/ablation`)
        if (res.ok) {
          const data = await res.json()
          fileContent = format === 'json'
            ? JSON.stringify({ title: PAGE_LABELS[page], timestamp: new Date().toISOString(), data }, null, 2)
            : convertJsonToCsv(data, 'ablation')
          fileName += format === 'csv' ? '.csv' : '.json'
        }
      } else {
        fileContent = JSON.stringify({
          title: `CloudGuard ${PAGE_LABELS[page]} Report`,
          timestamp: new Date().toISOString(),
          page: page,
          note: 'Export from CloudGuard AI Security Analysis System. Extended from OPMonitor (Wang et al., 2025)'
        }, null, 2)
        fileName += '.json'
      }

      const blob = new Blob([fileContent], { type: mimeType })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  // Helper to convert JSON to CSV format
  const convertJsonToCsv = (data: any, type: string): string => {
    if (type === 'baseline' && data.coarse_rules) {
      const rules = data.coarse_rules || []
      if (rules.length === 0) return 'No rules generated'
      const headers = Object.keys(rules[0]).join(',')
      const rows = rules.map((r: any) => Object.values(r).map(v => `"${v}"`).join(','))
      return [headers, ...rows].join('\n')
    } else if (type === 'metrics' && typeof data === 'object') {
      const headers = Object.keys(data).join(',')
      const values = Object.values(data).join(',')
      return `${headers}\n${values}`
    } else if (type === 'ablation' && data.results) {
      const rows = Object.entries(data.results).map(([variant, result]: any) => [
        variant,
        result.mean?.precision || 0,
        result.mean?.recall || 0,
        result.mean?.f1_score || 0
      ])
      const headers = 'Variant,Precision,Recall,F1 Score'
      return [headers, ...rows.map((r: any) => r.join(','))].join('\n')
    }
    return JSON.stringify(data)
  }

  return (
    <div className="flex min-h-screen bg-[var(--bg)]">
      <Sidebar current={page} onChange={setPage} />

      {/* Main content area */}
      <main className="min-h-screen flex flex-col flex-1">

        {/* Topbar */}
        <header
          className="sticky top-0 z-30 flex items-center justify-between px-8 py-4 border-b border-[var(--border)] bg-[var(--bg-1)]/80 backdrop-blur-md"
        >
          <div>
            <h1 className="text-sm font-semibold text-[var(--tx-1)]">{PAGE_LABELS[page]}</h1>
            <p className="text-[10px] font-mono text-[var(--tx-3)] mt-0.5">
              CloudGuard · AI-Powered Cloud Misconfiguration Detection
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 relative">
            {/* Export button with dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="px-3 py-2 text-xs font-medium rounded bg-[var(--am)]/10 hover:bg-[var(--am)]/20 text-[var(--am)] flex items-center gap-2 transition"
              >
                <Download size={14} /> Export
              </button>
              
              {showExportMenu && (
                <div className="absolute right-0 mt-1 w-44 rounded border border-[var(--border)] bg-[var(--bg-1)] shadow-xl z-50">
                  <button
                    onClick={() => handleExport('json')}
                    className="w-full px-4 py-2 text-xs text-left hover:bg-[var(--bg-2)] transition border-b border-[var(--border)] last:border-b-0 flex items-center gap-2 text-[var(--tx-1)]"
                  >
                    <FileJson size={14} className="text-[var(--am)]" /> Export as JSON
                  </button>
                  <button
                    onClick={() => handleExport('csv')}
                    className="w-full px-4 py-2 text-xs text-left hover:bg-[var(--bg-2)] transition border-b border-[var(--border)] last:border-b-0 flex items-center gap-2 text-[var(--tx-1)]"
                  >
                    <BarChart3 size={14} className="text-[var(--am)]" /> Export as CSV
                  </button>
                </div>
              )}
            </div>

            {/* Breadcrumb */}
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--tx-3)]">
              <span>cloudguard</span>
              <span>/</span>
              <span className="text-[var(--am)]">{page}</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-8 flex-1 flex flex-col">
          <Suspense fallback={
            <div className="flex items-center justify-center flex-1">
              <div className="text-[var(--tx-3)] animate-pulse">Loading analysis...</div>
            </div>
          }>
            {renderPage()}
          </Suspense>
        </div>

        {/* Footer */}
        <footer className="px-8 py-4 border-t border-[var(--border)] flex items-center justify-between mt-auto bg-[var(--bg-1)]/50">
          <p className="text-[10px] font-mono text-[var(--tx-3)]">
            CloudGuard — Extended from OPMonitor (Wang et al., 2025)
          </p>
          <p className="text-[10px] font-mono text-[var(--tx-3)]">
            Backend: <span className="text-[var(--grn)]">{API_BASE.replace(/^https?:\/\//, '')}</span>
          </p>
        </footer>
      </main>
    </div>
  )
}