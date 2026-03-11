import { useEffect, useRef, useState } from 'react'
import { Server, X } from 'lucide-react'
import { api } from '../api/client'
import type { Service } from '../types'

interface ServiceFormModalProps {
  /** If provided, the modal operates in edit mode; otherwise create mode. */
  service?: Service
  onClose: () => void
  onSaved: (service: Service) => void
}

export function ServiceFormModal({ service, onClose, onSaved }: ServiceFormModalProps) {
  const isEdit = !!service

  const [name, setName] = useState(service?.name ?? '')
  const [command, setCommand] = useState(service?.command ?? '')
  const [cwd, setCwd] = useState(service?.cwd ?? '.')
  const [portStr, setPortStr] = useState(service?.port != null ? String(service.port) : '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const nameRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    nameRef.current?.focus()
  }, [])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !command.trim()) return

    setLoading(true)
    setError(null)

    const port = portStr.trim() ? parseInt(portStr.trim(), 10) : null

    try {
      let saved: Service
      if (isEdit) {
        saved = await api.updateService(service.id, {
          name: name.trim(),
          command: command.trim(),
          cwd: cwd.trim() || '.',
          port: port ?? undefined,
          clear_port: portStr.trim() === '' && service.port != null,
        })
      } else {
        saved = await api.createService({
          name: name.trim(),
          command: command.trim(),
          cwd: cwd.trim() || '.',
          port,
        })
      }
      onSaved(saved)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save service')
    }
    setLoading(false)
  }

  const inputClass = `
    w-full bg-surface-850 border border-surface-700 rounded-xl
    px-4 py-3 text-sm text-white placeholder-gray-500
    transition-all duration-200
    focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
  `

  return (
    <div
      className="modal-backdrop animate-fade-in p-6"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="service-form-title"
    >
      <div
        className="modal-content w-full max-w-lg flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/15 border border-purple-500/20">
              <Server className="w-5 h-5 text-purple-400" />
            </div>
            <h2 id="service-form-title" className="text-lg font-semibold text-white">
              {isEdit ? 'Edit Service' : 'Add Service'}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 pb-6 flex flex-col gap-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Name <span className="text-red-400">*</span>
            </label>
            <input
              ref={nameRef}
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g., Next.js Frontend"
              className={inputClass}
              required
            />
          </div>

          {/* Command */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Command <span className="text-red-400">*</span>
            </label>
            <textarea
              value={command}
              onChange={e => setCommand(e.target.value)}
              placeholder="e.g., npm run dev"
              rows={2}
              className={`${inputClass} resize-none font-mono`}
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Shell command to start the service. Relative to Working Directory.
            </p>
          </div>

          {/* Working Directory + Port (side by side) */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Working Directory
              </label>
              <input
                type="text"
                value={cwd}
                onChange={e => setCwd(e.target.value)}
                placeholder="."
                className={inputClass}
              />
              <p className="mt-1 text-xs text-gray-500">Relative to project root.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Port
                <span className="text-gray-500 font-normal"> (optional)</span>
              </label>
              <input
                type="number"
                value={portStr}
                onChange={e => setPortStr(e.target.value)}
                placeholder="e.g., 3000"
                min={1}
                max={65535}
                className={inputClass}
              />
              <p className="mt-1 text-xs text-gray-500">Auto-detected if omitted.</p>
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2">
              {error}
            </p>
          )}

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-sm font-medium rounded-xl text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || !command.trim() || loading}
              className="px-5 py-2.5 text-sm font-medium rounded-xl bg-gradient-to-r from-purple-600 to-purple-500 text-white shadow-sm hover:from-purple-500 hover:to-purple-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 active:scale-[0.98]"
            >
              {loading ? (isEdit ? 'Saving…' : 'Adding…') : (isEdit ? 'Save Changes' : 'Add Service')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
