'use client'
import { useState, useEffect } from 'react'
import { Download, Upload, AlertTriangle, CheckCircle2, Zap } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

interface Config {
  id: string
  name: string
  type: 'iam' | 'k8s'
  risk_score: number | null
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'MINIMAL' | null
  uploaded_at: string
  analyzed: boolean
  issues: { pattern: string; severity: string; suggestion: string }[]
}

interface ScanResult {
  config_id: string
  config_name: string
  risk_score: number
  risk_level: string
  issues: { pattern: string; severity: string; suggestion: string }[]
  timestamp: string
}

export function ConfigUploadPage() {
  const [configs, setConfigs] = useState<Config[]>([])
  const [selectedConfig, setSelectedConfig] = useState<any>(null)
  const [scanning, setScanning] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [configType, setConfigType] = useState<'iam' | 'k8s'>('iam')
  const [scanResults, setScanResults] = useState<ScanResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Fetch configs from backend
  useEffect(() => {
    fetchConfigs()
  }, [])

  // Clear messages after 5 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [successMessage])

  const fetchConfigs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/config/list`)
      if (res.ok) {
        const data = await res.json()
        console.log('API response:', data) // DEBUG
        // Transform MongoDB response to match Config interface
        // Backend returns 'configs', not 'configurations'
        const configList = data.configs || data.configurations || data || []
        const transformed = configList.map((cfg: any) => ({
          id: cfg._id || cfg.id,
          name: cfg.name,
          type: cfg.config_type || cfg.type,
          risk_score: cfg.risk_score || null,
          risk_level: cfg.risk_level || null,
          uploaded_at: cfg.uploaded_at,
          analyzed: cfg.analyzed || false,
          issues: []
        }))
        console.log('Transformed configs:', transformed) // DEBUG
        setConfigs(transformed)
        setError(null)
      } else {
        setError('Failed to load configurations from backend')
      }
    } catch (err) {
      console.error('Failed to fetch configs:', err)
      setError('Backend is not responding. Make sure Flask server is running on http://localhost:5000')
      // Fallback to demo data if backend fails
      const demoConfigs: Config[] = [
        {
          id: '001',
          name: 'prod-iam-policy',
          type: 'iam',
          risk_score: 9.2,
          risk_level: 'CRITICAL',
          uploaded_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          analyzed: true,
          issues: []
        },
        {
          id: '002',
          name: 'staging-k8s-manifest',
          type: 'k8s',
          risk_score: 4.5,
          risk_level: 'MEDIUM',
          uploaded_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          analyzed: true,
          issues: []
        }
      ]
      setConfigs(demoConfigs)
    }
    setLoading(false)
  }

  const fetchConfigDetails = async (configId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/config/${configId}`)
      if (res.ok) {
        const details = await res.json()
        setSelectedConfig(details)
      }
    } catch (err) {
      console.error('Failed to fetch config details:', err)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) setSelectedFile(file)
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploading(true)
    setError(null)
    try {
      const text = await selectedFile.text()
      const res = await fetch(`${API_BASE}/api/config/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config_type: configType,
          config_name: selectedFile.name.replace(/\.[^.]+$/, ''),
          config_text: text,
          environment: 'prod'
        })
      })
      if (res.ok) {
        const uploadRes = await res.json()
        setSelectedFile(null)
        setSuccessMessage(`✓ Uploaded ${uploadRes.config_name} successfully`)
        await fetchConfigs()
      } else {
        const errorData = await res.json().catch(() => ({}))
        setError(`Upload failed: ${errorData.error || res.statusText}`)
      }
    } catch (err) {
      setError(`Upload error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      console.error('Upload failed:', err)
    }
    setUploading(false)
  }

  const handleScan = async (configId: string) => {
    setScanning(configId)
    setError(null)
    try {
      // Call backend scan endpoint
      const res = await fetch(`${API_BASE}/api/config/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config_ids: [configId],
          run_autoencoder: false
        })
      })
      
      if (res.ok) {
        const scanData = await res.json()
        if (scanData.scan_results && scanData.scan_results.length > 0) {
          const result = scanData.scan_results[0]
          // Create ScanResult from response
          const scanResult: ScanResult = {
            config_id: result.config_id,
            config_name: result.config_name,
            risk_score: result.risk_score?.risk_score || 0,
            risk_level: result.risk_score?.risk_level || 'MINIMAL',
            issues: [],
            timestamp: new Date().toISOString()
          }
          setScanResults([scanResult, ...scanResults])
        }
        // Refresh configs list to show updated scores
        await fetchConfigs()
      } else {
        const errorData = await res.json().catch(() => ({}))
        setError(`Scan failed: ${errorData.error || res.statusText}`)
      }
    } catch (err) {
      setError(`Scan error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      console.error('Scan failed:', err)
    }
    setScanning(null)
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
    <div className="space-y-6 p-8">
      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500 rounded text-red-400 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">✕</button>
        </div>
      )}

      {/* Success Alert */}
      {successMessage && (
        <div className="p-4 bg-green-500/10 border border-green-500 rounded text-green-400 text-sm">
          {successMessage}
        </div>
      )}

      {/* Upload Section */}
      <div className="card p-6 border border-[var(--border)]">
        <h2 className="text-lg font-semibold text-[var(--tx-1)] mb-4">Upload Configuration</h2>
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm text-[var(--tx-2)] mb-2">Configuration Type</label>
            <select 
              value={configType} 
              onChange={(e) => setConfigType(e.target.value as any)}
              className="w-full bg-[var(--bg-2)] border border-[var(--border)] text-[var(--tx-1)] px-3 py-2 rounded text-sm"
            >
              <option value="iam">IAM Policy (JSON)</option>
              <option value="k8s">Kubernetes Manifest (YAML)</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm text-[var(--tx-2)] mb-2">Select File</label>
            <input 
              type="file" 
              onChange={handleFileSelect}
              accept=".json,.yaml,.yml"
              className="w-full text-sm text-[var(--tx-3)]"
            />
          </div>
          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="px-4 py-2 bg-[var(--am)] text-black rounded font-medium hover:bg-[var(--am)] hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
          >
            <Upload size={16} /> {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </div>

      {/* Configs List */}
      <div className="card p-6 border border-[var(--border)]">
        <h2 className="text-lg font-semibold text-[var(--tx-1)] mb-4">Recent Configurations</h2>
        <div className="space-y-3">
          {loading ? (
            <p className="text-[var(--tx-3)]">Loading configurations...</p>
          ) : configs.length === 0 ? (
            <p className="text-[var(--tx-3)]">No configurations uploaded yet. Upload an IAM policy or Kubernetes manifest to get started.</p>
          ) : (
            configs.map(config => (
              <div 
                key={config.id} 
                className={`p-4 rounded border flex justify-between items-start cursor-pointer hover:shadow-md transition ${
                  config.analyzed 
                    ? 'bg-[var(--bg-2)] border-[var(--border)] hover:bg-[var(--bg-3)]' 
                    : 'bg-amber-500/5 border-amber-500/30 hover:bg-amber-500/10'
                }`}
                onClick={() => fetchConfigDetails(config.id)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-[var(--tx-1)]">{config.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${config.type === 'iam' ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'}`}>
                      {config.type.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[var(--tx-3)]">
                    <span>{new Date(config.uploaded_at).toLocaleDateString()}</span>
                    <span>•</span>
                    {config.analyzed && config.risk_score !== null && config.risk_level ? (
                      <span className={`font-semibold ${getRiskColor(config.risk_level)}`}>
                        {config.risk_level} ({config.risk_score.toFixed(1)}/10)
                      </span>
                    ) : (
                      <span className="text-amber-400 font-semibold">⚠ Not analyzed</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleScan(config.id)}
                  disabled={scanning === config.id}
                  className={`px-3 py-1 text-sm rounded font-medium ${
                    config.analyzed 
                      ? 'bg-[var(--am)]/10 hover:bg-[var(--am)]/20 text-[var(--am)]' 
                      : 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 font-bold'
                  } disabled:opacity-50`}
                >
                  {scanning === config.id ? 'Scanning...' : config.analyzed ? 'Rescan' : 'Scan Now'}
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Scan Results */}
      {scanResults.length > 0 && (
        <div className="card p-6 border border-[var(--border)]">
          <h2 className="text-lg font-semibold text-[var(--tx-1)] mb-4">Scan Results</h2>
          <div className="space-y-4">
            {scanResults.map(result => (
              <div key={result.config_id} className="p-4 bg-[var(--bg-2)] rounded border border-[var(--border)]">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-[var(--tx-1)]">{result.config_name}</h3>
                    <p className="text-xs text-[var(--tx-3)]">{new Date(result.timestamp).toLocaleString()}</p>
                  </div>
                  <div className={`text-2xl font-bold ${getRiskColor(result.risk_level)}`}>
                    {result.risk_score.toFixed(1)}
                  </div>
                </div>
                {result.issues.length > 0 && (
                  <div className="space-y-2">
                    {result.issues.map((issue, i) => (
                      <div key={i} className="text-sm p-2 bg-red-500/5 border border-red-500/20 rounded">
                        <p className="font-semibold text-red-400">{issue.pattern}</p>
                        <p className="text-[var(--tx-3)] text-xs">{issue.suggestion}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Details Panel */}
      {selectedConfig && (
        <div className="card p-6 border border-[var(--border)] fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[var(--bg-1)] rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 border border-[var(--border)]">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-[var(--tx-1)]">{selectedConfig.name}</h2>
                <p className="text-sm text-[var(--tx-3)]">
                  {selectedConfig.config_type?.toUpperCase()} • Analyzed: {new Date(selectedConfig.last_analyzed || selectedConfig.uploaded_at).toLocaleString()}
                </p>
              </div>
              <button 
                onClick={() => setSelectedConfig(null)}
                className="text-2xl text-[var(--tx-3)] hover:text-[var(--tx-1)]"
              >
                ✕
              </button>
            </div>

            {/* Risk Score Summary */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-[var(--bg-2)] rounded border border-[var(--border)]">
                <p className="text-xs text-[var(--tx-3)] mb-1">Risk Level</p>
                <p className={`text-2xl font-bold ${getRiskColor(selectedConfig.risk_level)}`}>
                  {selectedConfig.risk_level}
                </p>
              </div>
              <div className="p-4 bg-[var(--bg-2)] rounded border border-[var(--border)]">
                <p className="text-xs text-[var(--tx-3)] mb-1">Risk Score</p>
                <p className="text-2xl font-bold text-[var(--am)]">{selectedConfig.risk_score?.toFixed(1) || 'N/A'}/10</p>
              </div>
              <div className="p-4 bg-[var(--bg-2)] rounded border border-[var(--border)]">
                <p className="text-xs text-[var(--tx-3)] mb-1">Status</p>
                <p className="text-2xl font-bold text-green-400">{selectedConfig.analyzed ? '✓ Analyzed' : '⚠ Pending'}</p>
              </div>
            </div>

            {/* Remediation Actions */}
            {selectedConfig.remediation && (
              <div className="mb-6">
                <h3 className="font-semibold text-[var(--tx-1)] mb-3 flex items-center gap-2">
                  <AlertTriangle size={16} className="text-orange-500" />
                  Remediation Actions ({selectedConfig.remediation.total_issues || 0} issues)
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {selectedConfig.remediation.action_plan?.map((action: any, i: number) => (
                    <div key={i} className="p-3 bg-[var(--bg-2)] rounded border border-[var(--border)] text-sm">
                      <div className="flex items-start gap-3">
                        <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          action.severity === 'CRITICAL' ? 'bg-red-500 text-white' :
                          action.severity === 'HIGH' ? 'bg-orange-500 text-white' :
                          action.severity === 'MEDIUM' ? 'bg-yellow-500 text-black' :
                          'bg-blue-500 text-white'
                        }`}>
                          {action.priority}
                        </span>
                        <div className="flex-1">
                          <p className="text-[var(--tx-1)] font-medium">{action.action}</p>
                          <p className="text-xs text-[var(--tx-3)] mt-1">Issue: {action.issue} • {action.severity}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risk Factors */}
            {selectedConfig.explanation?.risk_factors && (
              <div className="mb-6">
                <h3 className="font-semibold text-[var(--tx-1)] mb-3 flex items-center gap-2">
                  <Zap size={16} className="text-yellow-500" />
                  Risk Factors ({selectedConfig.explanation.risk_factors.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {selectedConfig.explanation.risk_factors.map((factor: any, i: number) => (
                    <div key={i} className="p-3 bg-[var(--bg-2)] rounded border border-[var(--border)] text-sm">
                      <p className="font-semibold text-[var(--tx-1)]">{factor.factor}</p>
                      <p className="text-[var(--tx-3)] text-xs mt-1">{factor.remediation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Analysis Details */}
            {selectedConfig.analysis && (
              <div>
                <h3 className="font-semibold text-[var(--tx-1)] mb-3 flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-green-500" />
                  Configuration Analysis
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {selectedConfig.analysis.privilege_level && (
                    <div className="p-2 bg-[var(--bg-2)] rounded">
                      <p className="text-[var(--tx-3)]">Privilege Level</p>
                      <p className="font-semibold text-[var(--tx-1)]">{selectedConfig.analysis.privilege_level}</p>
                    </div>
                  )}
                  {selectedConfig.analysis.is_public !== undefined && (
                    <div className="p-2 bg-[var(--bg-2)] rounded">
                      <p className="text-[var(--tx-3)]">Public Access</p>
                      <p className="font-semibold text-[var(--tx-1)]">{selectedConfig.analysis.is_public ? '⚠ Yes' : '✓ No'}</p>
                    </div>
                  )}
                  {selectedConfig.analysis.config_type && (
                    <div className="p-2 bg-[var(--bg-2)] rounded">
                      <p className="text-[var(--tx-3)]">Config Type</p>
                      <p className="font-semibold text-[var(--tx-1)]">{selectedConfig.analysis.config_type.toUpperCase()}</p>
                    </div>
                  )}
                  {selectedConfig.analysis.sensitive_resources && (
                    <div className="p-2 bg-[var(--bg-2)] rounded">
                      <p className="text-[var(--tx-3)]">Sensitive Resources</p>
                      <p className="font-semibold text-[var(--tx-1)]">{selectedConfig.analysis.sensitive_resources.length} found</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
