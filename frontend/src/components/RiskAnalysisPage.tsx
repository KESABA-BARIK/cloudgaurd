'use client'
import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle2, Lightbulb, TrendingUp, Copy, Check } from 'lucide-react'

interface Issue {
  id: string
  pattern: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  description: string
  remediation: string
  impact: string
}

interface RiskItem {
  id: string
  name: string
  type: string
  risk_score: number
  risk_level: string
  issues: Issue[]
}

export function RiskAnalysisPage() {
  const [risks, setRisks] = useState<RiskItem[]>([])
  const [selectedRisk, setSelectedRisk] = useState<RiskItem | null>(null)
  const [copiedIssueId, setCopiedIssueId] = useState<string | null>(null)

  // Demo data
  useEffect(() => {
    const demoRisks: RiskItem[] = [
      {
        id: '1',
        name: 'prod-iam-policy',
        type: 'IAM Policy',
        risk_score: 9.2,
        risk_level: 'CRITICAL',
        issues: [
          {
            id: 'i1',
            pattern: 'S3:* on All Resources',
            severity: 'CRITICAL',
            description: 'IAM policy grants full S3 access to all resources without restrictions',
            remediation: 'Replace with specific bucket ARNs: arn:aws:s3:::specific-bucket/*',
            impact: 'Could lead to unauthorized data access, deletion, or modification'
          },
          {
            id: 'i2',
            pattern: 'Overly Permissive Actions',
            severity: 'CRITICAL',
            description: 'Multiple action wildcards detected',
            remediation: 'Specify only required actions (GetObject, PutObject, etc.)',
            impact: 'Increases attack surface significantly'
          }
        ]
      },
      {
        id: '2',
        name: 'staging-k8s',
        type: 'Kubernetes Manifest',
        risk_score: 4.5,
        risk_level: 'MEDIUM',
        issues: [
          {
            id: 'i3',
            pattern: 'Privileged Container',
            severity: 'HIGH',
            description: 'Container running in privileged mode',
            remediation: 'Set securityContext.privileged: false in pod spec',
            impact: 'Container has access to host resources, kernel capabilities'
          }
        ]
      }
    ]
    setRisks(demoRisks)
    if (demoRisks.length > 0) setSelectedRisk(demoRisks[0])
  }, [])

  const handleApplyRemediation = (issueId: string, remediationText: string) => {
    // Copy remediation to clipboard
    navigator.clipboard.writeText(remediationText).then(() => {
      setCopiedIssueId(issueId)
      // Reset after 2 seconds
      setTimeout(() => setCopiedIssueId(null), 2000)
    })
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400' }
      case 'HIGH': return { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400' }
      case 'MEDIUM': return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400' }
      default: return { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400' }
    }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'text-red-500'
      case 'HIGH': return 'text-orange-500'
      case 'MEDIUM': return 'text-yellow-500'
      case 'LOW': return 'text-blue-500'
      default: return 'text-green-500'
    }
  }

  return (
    <div className="grid grid-cols-3 gap-6 p-8 h-screen overflow-hidden">
      {/* Left: Risk List */}
      <div className="col-span-1 flex flex-col">
        <h2 className="text-lg font-semibold text-[var(--tx-1)] mb-4">Analyzed Configs</h2>
        <div className="flex-1 overflow-y-auto space-y-3 pr-4">
          {risks.map(risk => (
            <div
              key={risk.id}
              onClick={() => setSelectedRisk(risk)}
              className={`p-4 rounded border cursor-pointer transition ${
                selectedRisk?.id === risk.id
                  ? 'bg-[var(--am-bg)] border-[var(--am-border)]'
                  : 'bg-[var(--bg-2)] border-[var(--border)] hover:border-[var(--am-border)]'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-[var(--tx-1)] text-sm">{risk.name}</h3>
                  <p className="text-xs text-[var(--tx-3)]">{risk.type}</p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className={`text-sm font-bold ${getRiskColor(risk.risk_level)}`}>
                  {risk.risk_score.toFixed(1)}/10
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-[var(--border)] text-[var(--tx-3)]">
                  {risk.issues.length} issues
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Risk Details */}
      <div className="col-span-2 flex flex-col">
        {selectedRisk ? (
          <>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h1 className="text-2xl font-bold text-[var(--tx-1)]">{selectedRisk.name}</h1>
                <div className={`text-3xl font-bold ${getRiskColor(selectedRisk.risk_level)}`}>
                  {selectedRisk.risk_score.toFixed(1)}
                </div>
              </div>
              <p className="text-sm text-[var(--tx-2)]">{selectedRisk.type}</p>
            </div>

            {/* Issues */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-4">
              {selectedRisk.issues.map(issue => {
                const colors = getSeverityColor(issue.severity)
                return (
                  <div key={issue.id} className={`p-4 rounded border ${colors.bg} ${colors.border}`}>
                    <div className="flex items-start gap-3 mb-3">
                      <AlertTriangle size={18} className={colors.text} />
                      <div className="flex-1">
                        <h3 className={`font-semibold ${colors.text}`}>{issue.pattern}</h3>
                        <span className={`text-xs font-semibold ${colors.text}`}>{issue.severity}</span>
                      </div>
                    </div>

                    <p className="text-sm text-[var(--tx-2)] mb-3">{issue.description}</p>

                    <div className="space-y-2 mb-3">
                      <div className="flex gap-2">
                        <Lightbulb size={14} className="text-[var(--am)] flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-semibold text-[var(--tx-1)]">Remediation</p>
                          <p className="text-xs text-[var(--tx-2)]">{issue.remediation}</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <TrendingUp size={14} className="text-orange-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-semibold text-[var(--tx-1)]">Security Impact</p>
                          <p className="text-xs text-[var(--tx-2)]">{issue.impact}</p>
                        </div>
                      </div>
                    </div>

                    <button 
                      onClick={() => handleApplyRemediation(issue.id, issue.remediation)}
                      className={`w-full py-1.5 rounded transition text-xs font-semibold flex items-center justify-center gap-2 ${
                        copiedIssueId === issue.id
                          ? 'bg-[var(--grn)]/20 text-[var(--grn)]'
                          : 'bg-[var(--am)]/10 hover:bg-[var(--am)]/20 text-[var(--am)]'
                      }`}
                    >
                      {copiedIssueId === issue.id ? (
                        <>
                          <Check size={13} /> Copied to Clipboard
                        </>
                      ) : (
                        <>
                          <Copy size={13} /> Copy Remediation
                        </>
                      )}
                    </button>
                  </div>
                )
              })}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-[var(--tx-3)]">Select a configuration to view details</p>
          </div>
        )}
      </div>
    </div>
  )
}
