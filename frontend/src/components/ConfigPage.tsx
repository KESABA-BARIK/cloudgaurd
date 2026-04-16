'use client'
import { useState, useEffect } from 'react'
import { Download, Upload, AlertTriangle, CheckCircle2, Zap } from 'lucide-react'

interface Config {
  id: string
  name: string
  type: 'iam' | 'k8s'
  risk_score: number
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'MINIMAL'
  uploaded_at: string
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
  const [scanning, setScanning] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [configType, setConfigType] = useState<'iam' | 'k8s'>('iam')
  const [scanResults, setScanResults] = useState<ScanResult[]>([])

  // Demo data
  useEffect(() => {
    const demoConfigs: Config[] = [
      {
        id: '001',
        name: 'prod-iam-policy',
        type: 'iam',
        risk_score: 9.2,
        risk_level: 'CRITICAL',
        uploaded_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        issues: [
          { pattern: 'S3:*', severity: 'Critical', suggestion: 'Restrict to specific buckets' },
          { pattern: 'Public Access', severity: 'Critical', suggestion: 'Add IP restrictions' },
        ]
      },
      {
        id: '002',
        name: 'staging-k8s-manifest',
        type: 'k8s',
        risk_score: 4.5,
        risk_level: 'MEDIUM',
        uploaded_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        issues: [
          { pattern: 'Privileged Container', severity: 'Medium', suggestion: 'Set securityContext.privileged=false' },
        ]
      }
    ]
    setConfigs(demoConfigs)
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) setSelectedFile(file)
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploading(true)
    try {
      const text = await selectedFile.text()
      const newConfig: Config = {
        id: String(Date.now()),
        name: selectedFile.name.replace(/\.[^.]+$/, ''),
        type: configType,
        risk_score: Math.random() * 10,
        risk_level: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL'][Math.floor(Math.random() * 5)] as any,
        uploaded_at: new Date().toISOString(),
        issues: []
      }
      setConfigs([newConfig, ...configs])
      setSelectedFile(null)
    } catch (err) {
      console.error('Upload failed:', err)
    }
    setUploading(false)
  }

  const handleScan = async (configId: string) => {
    setScanning(true)
    try {
      const config = configs.find(c => c.id === configId)
      if (!config) return
      
      const result: ScanResult = {
        config_id: configId,
        config_name: config.name,
        risk_score: config.risk_score,
        risk_level: config.risk_level,
        issues: config.issues,
        timestamp: new Date().toISOString()
      }
      setScanResults([result, ...scanResults])
    } catch (err) {
      console.error('Scan failed:', err)
    }
    setScanning(false)
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
            <Upload size={16} /> Upload
          </button>
        </div>
      </div>

      {/* Configs List */}
      <div className="card p-6 border border-[var(--border)]">
        <h2 className="text-lg font-semibold text-[var(--tx-1)] mb-4">Recent Configurations</h2>
        <div className="space-y-3">
          {configs.map(config => (
            <div key={config.id} className="p-4 bg-[var(--bg-2)] rounded border border-[var(--border)] flex justify-between items-start">
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
                  <span className={`font-semibold ${getRiskColor(config.risk_level)}`}>
                    {config.risk_level} ({config.risk_score.toFixed(1)}/10)
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleScan(config.id)}
                disabled={scanning}
                className="px-3 py-1 bg-[var(--am)]/10 hover:bg-[var(--am)]/20 text-[var(--am)] text-sm rounded font-medium"
              >
                {scanning ? 'Scanning...' : 'Scan'}
              </button>
            </div>
          ))}
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
    </div>
  )
}
