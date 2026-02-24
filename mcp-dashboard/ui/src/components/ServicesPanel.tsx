import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronDown, ChevronRight, ExternalLink, Play, RefreshCw, Server, Square } from 'lucide-react'
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

function ServiceRow({ service }: { service: Service }) {
  const [expanded, setExpanded] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
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
    if (expanded && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, expanded])

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

  return (
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

      {/* Expandable log viewer */}
      {expanded && (
        <div className="border-t border-surface-800/50 bg-surface-925 max-h-64 overflow-y-auto">
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
    </div>
  )
}

export function ServicesPanel() {
  const { state } = useDashboard()
  const { services } = state

  const runningCount = services.filter(s => s.status === 'running').length

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
