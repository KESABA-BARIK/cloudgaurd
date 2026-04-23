/**
 * Export utilities for CloudGuard
 * Supports JSON, CSV, and markdown formats
 */

export interface ReportData {
  title: string
  timestamp: string
  data: any
  summary?: string
}

/**
 * Export data as JSON
 */
export function exportAsJSON(data: ReportData, filename?: string) {
  const json = JSON.stringify(data, null, 2)
  downloadFile(json, filename || `report-${Date.now()}.json`, 'application/json')
}

/**
 * Export data as CSV
 */
export function exportAsCSV(data: any[], filename?: string) {
  if (!data || data.length === 0) return

  // Get headers from first object
  const headers = Object.keys(data[0])
  
  // Create CSV content
  let csv = headers.join(',') + '\n'
  data.forEach(row => {
    const values = headers.map(h => {
      const val = row[h]
      // Escape quotes and wrap in quotes if contains comma
      if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
        return `"${val.replace(/"/g, '""')}"`
      }
      return val
    })
    csv += values.join(',') + '\n'
  })

  downloadFile(csv, filename || `report-${Date.now()}.csv`, 'text/csv')
}

/**
 * Export data as Markdown
 */
export function exportAsMarkdown(data: ReportData, filename?: string) {
  let md = `# ${data.title}\n\n`
  md += `**Generated:** ${new Date(data.timestamp).toLocaleString()}\n\n`
  
  if (data.summary) {
    md += `## Summary\n${data.summary}\n\n`
  }

  md += `## Data\n\`\`\`json\n${JSON.stringify(data.data, null, 2)}\n\`\`\`\n`

  downloadFile(md, filename || `report-${Date.now()}.md`, 'text/markdown')
}

/**
 * Download file helper
 */
function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Generate risk analysis report
 */
export function generateRiskReport(configs: any[]) {
  const criticalCount = configs.filter(c => c.risk_level === 'CRITICAL').length
  const highCount = configs.filter(c => c.risk_level === 'HIGH').length
  const avgRisk = configs.reduce((sum, c) => sum + c.risk_score, 0) / configs.length

  return {
    title: 'CloudGuard Risk Analysis Report',
    timestamp: new Date().toISOString(),
    summary: `Found ${configs.length} configurations. Critical: ${criticalCount}, High: ${highCount}. Average Risk Score: ${avgRisk.toFixed(2)}/10`,
    data: configs
  }
}

/**
 * Generate compliance report
 */
export function generateComplianceReport(findings: any[]) {
  const byPattern = findings.reduce((acc, f) => {
    acc[f.pattern] = (acc[f.pattern] || 0) + 1
    return acc
  }, {})

  return {
    title: 'CloudGuard Compliance Report',
    timestamp: new Date().toISOString(),
    summary: `Analyzed ${findings.length} security findings across ${Object.keys(byPattern).length} pattern categories.`,
    data: { findings, patternSummary: byPattern }
  }
}
