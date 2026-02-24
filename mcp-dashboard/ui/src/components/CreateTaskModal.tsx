import { Plus, X } from 'lucide-react'
import { useState } from 'react'
import { api } from '../api/client'
import { useDashboard } from '../context/DashboardContext'

type CreateTaskModalProps = {
  onClose: () => void
}

export function CreateTaskModal({ onClose }: CreateTaskModalProps) {
  const { refreshTasks, refreshStats } = useDashboard()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [autoAccept, setAutoAccept] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    setLoading(true)
    try {
      await api.createTask(title.trim(), description.trim(), autoAccept)
      await refreshTasks()
      await refreshStats()
      onClose()
    } catch (err) {
      console.error('Failed to create task:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="modal-backdrop animate-fade-in p-6"
      onClick={onClose}
    >
      <div
        className="modal-content w-full max-w-md"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-accent-500/15 border border-accent-500/20">
              <Plus className="w-5 h-5 text-accent-400" />
            </div>
            <h2 className="text-lg font-semibold text-white">New Task</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 pb-6">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Title
              </label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="e.g., Build user authentication"
                className="
                  w-full bg-surface-850 border border-surface-700 rounded-xl
                  px-4 py-3 text-sm text-white placeholder-gray-500
                  transition-all duration-200
                  focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
                "
                autoFocus
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Detailed requirements..."
                rows={4}
                className="
                  w-full bg-surface-850 border border-surface-700 rounded-xl
                  px-4 py-3 text-sm text-white placeholder-gray-500
                  resize-none transition-all duration-200
                  focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
                "
              />
            </div>

            <label className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={autoAccept}
                  onChange={e => setAutoAccept(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="
                  w-5 h-5 rounded-md border border-surface-600 bg-surface-800
                  peer-checked:bg-accent-500 peer-checked:border-accent-500
                  transition-all duration-200
                  flex items-center justify-center
                ">
                  {autoAccept && (
                    <svg className="w-3 h-3 text-white" viewBox="0 0 12 10" fill="none">
                      <path d="M1 5L4.5 8.5L11 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </div>
              </div>
              <div className="flex-1">
                <span className="text-sm text-gray-300 group-hover:text-gray-200 transition-colors">
                  Auto-accept questions
                </span>
                <span className="text-xs text-gray-500 ml-2">(skip approval prompts)</span>
              </div>
            </label>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 mt-6 pt-5 border-t border-surface-800/50">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-medium text-gray-400 hover:text-white rounded-xl hover:bg-surface-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || loading}
              className="
                px-5 py-2.5 text-sm font-medium rounded-xl
                bg-gradient-to-r from-accent-600 to-accent-500 text-white
                shadow-glow-sm hover:from-accent-500 hover:to-accent-400
                disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
                transition-all duration-200 active:scale-[0.98]
              "
            >
              {loading ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
