import { useCallback, useEffect, useRef, useState } from 'react'
import {
  AlertTriangle, ChevronDown, ChevronRight, ExternalLink, Eye,
  Maximize2, Play, RefreshCw, Server, Square, Terminal, X,
} from 'lucide-react'
import { api } from '../api/client'
import { useDashboard } from '../context/DashboardContext'
import type { Service } from '../types'

const STATUS_CLASS: Record<Service['status'], string> = {
  running: 'status-dot-running',
  starting: 'status-dot-starting',
  stopped: 'status-dot-stopped',
  failed: 'status-dot-failed',
}

function formatUptime(seconds: number | null): string {
  if (seconds === null) return ''
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins < 60) return `${mins}m ${secs}s`
  const hrs = Math.floor(mins / 60)
  return `${hrs}h ${mins % 60}m`
}

type ExpandedTab = 'logs' | 'preview'

function ServiceInlinePreview({ port, onMaximize }: { port: number; onMaximize: () => void }) {
  const [status, setStatus] = useState<'loading' | 'loaded' | 'error'>('loading')
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [iframeKey, setIframeKey] = useState(0)
  const url = `http://localhost:${port}`

  const handleRefresh = () => {
    setStatus('loading')
    setIframeKey(k => k + 1)
  }

  return (
    <div className="relative" style={{ height: 240 }}>
      {/* Toolbar */}
      <div className="absolute top-0 right-0 z-10 flex items-center gap-1 p-1.5">
        <button
          onClick={handleRefresh}
          className="p-1 rounded-md bg-surface-800/80 text-gray-400 hover:text-gray-200 hover:bg-surface-700 transition-colors"
          title="Refresh"
        >
          <RefreshCw className="w-3 h-3" />
        </button>
        <button
          onClick={onMaximize}
          className="p-1 rounded-md bg-surface-800/80 text-gray-400 hover:text-gray-200 hover:bg-surface-700 transition-colors"
          title="Fullscreen"
        >
          <Maximize2 className="w-3 h-3" />
        </button>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="p-1 rounded-md bg-surface-800/80 text-gray-400 hover:text-gray-200 hover:bg-surface-700 transition-colors"
          title="Open in new tab"
        >
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* Loading spinner */}
      {status === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center bg-surface-925/80 z-[5]">
          <RefreshCw className="w-5 h-5 text-gray-500 animate-spin" />
        </div>
      )}

      {/* Error state */}
      {status === 'error' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-925 z-[5] gap-2">
          <AlertTriangle className="w-6 h-6 text-amber-500" />
          <p className="text-sm text-gray-400">Unable to load preview</p>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-accent-400 hover:text-accent-300 flex items-center gap-1"
          >
            Open in new tab <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      )}

      {/* iframe */}
      <iframe
        key={iframeKey}
        ref={iframeRef}
        src={url}
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        className="w-full h-full border-0 bg-white rounded-b-xl"
        onLoad={() => setStatus('loaded')}
        onError={() => setStatus('error')}
        title={`Preview localhost:${port}`}
      />
    </div>
  )
}

function ServicePreviewModal({ service, onClose }: { service: Service; onClose: () => void }) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [iframeKey, setIframeKey] = useState(0)
  const url = `http://localhost:${service.port}`

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const handleRefresh = () => {
    setIframeKey(k => k + 1)
  }

  return (
    <div
      className="modal-backdrop animate-fade-in p-8"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="preview-modal-title"
    >
      <div
        className="bg-surface-900 border border-surface-700/50 rounded-2xl shadow-modal animate-scale-in flex flex-col overflow-hidden"
        style={{ width: '90vw', height: '85vh' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-surface-800/50 shrink-0">
          <div className="flex items-center gap-2.5">
            <Eye className="w-4 h-4 text-accent-400" />
            <span id="preview-modal-title" className="text-sm font-semibold text-gray-100">
              {service.name}
            </span>
            <span className="text-xs text-gray-500">:{service.port}</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleRefresh}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-surface-800 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-surface-800 transition-colors"
              title="Open in new tab"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-surface-800 transition-colors"
              title="Close"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Body — iframe fills remaining space */}
        <div className="flex-1 overflow-hidden">
          <iframe
            key={iframeKey}
            ref={iframeRef}
            src={url}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
            className="w-full h-full border-0 bg-white"
            title={`Preview ${service.name} localhost:${service.port}`}
          />
        </div>
      </div>
    </div>
  )
}

function ServiceRow({ service }: { service: Service }) {
  const [expanded, setExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState<ExpandedTab>('logs')
  const [logs, setLogs] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const logEndRef = useRef<HTMLDivElement>(null)

  const fetchLogs = useCallback(async () => {
    try {
      const { logs: lines } = await api.getServiceLogs(service.id)
      setLogs(lines)
    } catch {
      // ignore
    }
  }, [service.id])

  useEffect(() => {
    if (!expanded) return
    fetchLogs()
    if (service.status === 'running') {
      const interval = setInterval(fetchLogs, 2000)
      return () => clearInterval(interval)
    }
  }, [expanded, service.status, fetchLogs])

  useEffect(() => {
    if (expanded && activeTab === 'logs' && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, expanded, activeTab])

  const handleStart = async () => {
    setLoading(true)
    try {
      await api.startService(service.id)
    } catch {
      // ignore
    }
    setLoading(false)
  }

  const handleStop = async () => {
    setLoading(true)
    try {
      await api.stopService(service.id)
    } catch {
      // ignore
    }
    setLoading(false)
  }

  const handleRestart = async () => {
    setLoading(true)
    try {
      await api.restartService(service.id)
    } catch {
      // ignore
    }
    setLoading(false)
  }

  const isRunning = service.status === 'running' || service.status === 'starting'
  const hasPreview = isRunning && !!service.port

  // Reset to logs tab when service stops or loses port
  useEffect(() => {
    if (!hasPreview && activeTab === 'preview') {
      setActiveTab('logs')
    }
  }, [hasPreview, activeTab])

  const handleEyeClick = () => {
    setExpanded(true)
    setActiveTab('preview')
  }

  return (
    <>
      <div className="bg-surface-900/60 border border-surface-800/50 rounded-xl overflow-hidden transition-all duration-200 hover:border-surface-700/50">
        {/* Header row */}
        <div className="flex items-center gap-3 px-4 py-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-surface-800 transition-colors"
          >
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>

          {/* Status dot */}
          <span className={STATUS_CLASS[service.status]} />

          {/* Name + info */}
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium text-gray-200 truncate block">{service.name}</span>
          </div>

          {/* Port */}
          {service.port && isRunning && (
            <a
              href={`http://localhost:${service.port}`}
              target="_blank"
              rel="noopener noreferrer"
              className="
                flex items-center gap-1 px-2 py-0.5 rounded-lg
                text-xs text-accent-400 bg-accent-500/10
                hover:bg-accent-500/20 transition-colors
              "
            >
              :{service.port}
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
          {service.port && !isRunning && (
            <span className="text-xs text-gray-600 px-2 py-0.5">:{service.port}</span>
          )}

          {/* Preview eye button */}
          {hasPreview && (
            <button
              onClick={handleEyeClick}
              className="p-1.5 rounded-lg text-accent-400 hover:bg-accent-500/15 hover:text-accent-300 transition-colors"
              title="Preview"
            >
              <Eye className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Uptime */}
          {service.uptime !== null && (
            <span className="text-xs text-gray-500 font-medium">{formatUptime(service.uptime)}</span>
          )}

          {/* Action buttons */}
          <div className="flex items-center gap-0.5">
            {!isRunning && (
              <button
                onClick={handleStart}
                disabled={loading}
                className="
                  p-1.5 rounded-lg text-emerald-400
                  hover:bg-emerald-500/15 hover:text-emerald-300
                  disabled:opacity-50 transition-colors
                "
                title="Start"
              >
                <Play className="w-3.5 h-3.5" />
              </button>
            )}
            {isRunning && (
              <>
                <button
                  onClick={handleRestart}
                  disabled={loading}
                  className="
                    p-1.5 rounded-lg text-amber-400
                    hover:bg-amber-500/15 hover:text-amber-300
                    disabled:opacity-50 transition-colors
                  "
                  title="Restart"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={handleStop}
                  disabled={loading}
                  className="
                    p-1.5 rounded-lg text-red-400
                    hover:bg-red-500/15 hover:text-red-300
                    disabled:opacity-50 transition-colors
                  "
                  title="Stop"
                >
                  <Square className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Expanded section */}
        {expanded && (
          <div className="border-t border-surface-800/50">
            {/* Tab bar — only when preview is available */}
            {hasPreview && (
              <div className="flex items-center justify-between px-4 py-0 border-b border-surface-800/50 bg-surface-900/40">
                <div className="flex items-center">
                  <button
                    onClick={() => setActiveTab('logs')}
                    className={`
                      flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors
                      ${activeTab === 'logs'
                        ? 'border-accent-400 text-accent-400'
                        : 'border-transparent text-gray-500 hover:text-gray-300'
                      }
                    `}
                  >
                    <Terminal className="w-3 h-3" />
                    Logs
                  </button>
                  <button
                    onClick={() => setActiveTab('preview')}
                    className={`
                      flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors
                      ${activeTab === 'preview'
                        ? 'border-accent-400 text-accent-400'
                        : 'border-transparent text-gray-500 hover:text-gray-300'
                      }
                    `}
                  >
                    <Eye className="w-3 h-3" />
                    Preview
                  </button>
                </div>
              </div>
            )}

            {/* Logs content */}
            {activeTab === 'logs' && (
              <div className="bg-surface-925 max-h-64 overflow-y-auto">
                {logs.length === 0 ? (
                  <div className="px-4 py-3 text-gray-600 italic text-sm">No logs available</div>
                ) : (
                  <div className="px-4 py-2.5 font-mono text-xs">
                    {logs.map((line, i) => (
                      <div key={i} className="text-gray-400 leading-6 whitespace-pre-wrap break-all">
                        {line}
                      </div>
                    ))}
                    <div ref={logEndRef} />
                  </div>
                )}
              </div>
            )}

            {/* Preview content */}
            {activeTab === 'preview' && hasPreview && (
              <div className="bg-surface-925">
                <ServiceInlinePreview
                  port={service.port!}
                  onMaximize={() => setShowPreviewModal(true)}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Preview modal */}
      {showPreviewModal && hasPreview && (
        <ServicePreviewModal
          service={service}
          onClose={() => setShowPreviewModal(false)}
        />
      )}
    </>
  )
}

export function ServicesPanel() {
  const { state } = useDashboard()
  const { services } = state
  const [reloading, setReloading] = useState(false)

  const runningCount = services.filter(s => s.status === 'running').length

  const handleReload = async () => {
    setReloading(true)
    try {
      await api.reloadServices()
    } catch (err) {
      console.error('Failed to reload services:', err)
    }
    setReloading(false)
  }

  return (
    <div className="w-[420px] border-l border-surface-800/50 bg-surface-900/95 backdrop-blur-md flex flex-col h-full animate-slide-in-right">
      {/* Header */}
      <div className="px-5 py-4 border-b border-surface-800/50">
        <div className="flex items-center gap-2.5">
          <Server className="w-4.5 h-4.5 text-purple-400" />
          <h2 className="text-sm font-semibold text-gray-100">Services</h2>
          <span className="ml-auto px-2 py-0.5 rounded-md bg-surface-800/80 text-xs text-gray-400">
            {runningCount}/{services.length}
          </span>
          <button
            onClick={handleReload}
            disabled={reloading}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-surface-800 disabled:opacity-50 transition-colors"
            title="Reload configuration"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reloading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Service list */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {services.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Server className="w-8 h-8 mb-3 opacity-40" />
            <p className="text-sm">No services configured</p>
            <p className="text-xs mt-1 text-gray-600">
              Add <code className="text-accent-400 bg-surface-800 px-1 py-0.5 rounded text-[10px]">services.json</code> to <code className="text-accent-400 bg-surface-800 px-1 py-0.5 rounded text-[10px]">.dashboard/</code>
            </p>
          </div>
        ) : (
          services.map((svc) => (
            <ServiceRow key={svc.id} service={svc} />
          ))
        )}
      </div>
    </div>
  )
}
