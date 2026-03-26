import { ChevronDown, Expand, FileText, GitBranch, ImagePlus, Minimize2, Plus, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'
import { useDashboard } from '../context/DashboardContext'
import type { Document } from '../types'

type CreateTaskModalProps = {
  onClose: () => void
}

export function CreateTaskModal({ onClose }: CreateTaskModalProps) {
  const { state, refreshTasks, refreshStats } = useDashboard()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [qaDetails, setQaDetails] = useState('')
  const [autoAccept, setAutoAccept] = useState(false)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [resumeSessionId, setResumeSessionId] = useState<string | null>(null)
  const [sessionDropdownOpen, setSessionDropdownOpen] = useState(false)
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set())
  const [availableDocs, setAvailableDocs] = useState<Document[]>([])
  const [pendingImages, setPendingImages] = useState<File[]>([])
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch available documents
  useEffect(() => {
    api.listDocuments().then(setAvailableDocs).catch(() => {})
  }, [])

  // Tasks that have a claude_session_id (completed, failed, or ran at least once)
  const tasksWithSessions = useMemo(() => {
    const collect = (tasks: typeof state.tasks): typeof state.tasks => {
      const result: typeof state.tasks = []
      for (const t of tasks) {
        if (t.claude_session_id) result.push(t)
        if (t.children?.length) result.push(...collect(t.children))
      }
      return result
    }
    return collect(state.tasks).sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  }, [state.tasks])

  const selectedSession = tasksWithSessions.find(t => t.claude_session_id === resumeSessionId)

  const docsByFolder = useMemo(() => {
    const map = new Map<string, Document[]>()
    for (const doc of availableDocs) {
      const folder = doc.folder || '(ungrouped)'
      if (!map.has(folder)) map.set(folder, [])
      map.get(folder)!.push(doc)
    }
    return map
  }, [availableDocs])

  const toggleDocSelection = (docId: string) => {
    setSelectedDocIds(prev => {
      const next = new Set(prev)
      if (next.has(docId)) next.delete(docId)
      else next.add(docId)
      return next
    })
  }

  const handleAddImages = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    // Copy into a plain array BEFORE clearing the input.
    // FileList is a live DOM object — clearing the input empties it in-place,
    // and React 18 batching may defer the state updater until after that happens.
    const fileArray = Array.from(files)
    e.target.value = ''
    setPendingImages(prev => [...prev, ...fileArray])
  }

  const removePendingImage = (index: number) => {
    setPendingImages(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    setLoading(true)
    try {
      const task = await api.createTask(title.trim(), description.trim(), autoAccept, resumeSessionId || undefined, selectedDocIds.size > 0 ? [...selectedDocIds] : undefined, qaDetails.trim() || undefined)
      // Upload pending images to the created task
      for (const file of pendingImages) {
        await api.uploadTaskImage(task.id, file)
      }
      await refreshTasks()
      await refreshStats()
      onClose()
    } catch (err) {
      console.error('Failed to create task:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatTimeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    const days = Math.floor(hrs / 24)
    return `${days}d ago`
  }

  const statusColor: Record<string, string> = {
    completed: 'text-emerald-400',
    failed: 'text-red-400',
    in_progress: 'text-amber-400',
    pending: 'text-gray-400',
    blocked: 'text-orange-400',
  }

  return (
    <div
      className="modal-backdrop animate-fade-in p-6"
      onClick={onClose}
    >
      <div
        className={`modal-content w-full transition-all duration-300 ${
          expanded ? 'max-w-5xl max-h-[90vh]' : 'max-w-2xl'
        } flex flex-col`}
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
          <div className="flex items-center gap-1">
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
              title={expanded ? 'Collapse' : 'Expand'}
            >
              {expanded ? <Minimize2 className="w-4 h-4" /> : <Expand className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 pb-6 flex flex-col flex-1 min-h-0">
          <div className="space-y-5 flex-1 overflow-y-auto min-h-0">
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
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-300">
                  Description
                </label>
                {description.trim() && (
                  <div className="flex items-center gap-1 bg-surface-800 rounded-lg p-0.5">
                    <button
                      type="button"
                      onClick={() => setShowPreview(false)}
                      className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                        !showPreview
                          ? 'bg-surface-700 text-white'
                          : 'text-gray-400 hover:text-gray-300'
                      }`}
                    >
                      Write
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowPreview(true)}
                      className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                        showPreview
                          ? 'bg-surface-700 text-white'
                          : 'text-gray-400 hover:text-gray-300'
                      }`}
                    >
                      Preview
                    </button>
                  </div>
                )}
              </div>
              {showPreview && description.trim() ? (
                <div
                  className={`bg-surface-850 border border-surface-700 rounded-xl px-4 py-3 overflow-y-auto artifact-markdown ${
                    expanded ? 'min-h-[300px] max-h-[50vh]' : 'min-h-[160px] max-h-[40vh]'
                  }`}
                >
                  <Markdown remarkPlugins={[remarkGfm]}>{description}</Markdown>
                </div>
              ) : (
                <textarea
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Detailed requirements... (supports Markdown)"
                  rows={expanded ? 14 : 8}
                  className={`
                    w-full bg-surface-850 border border-surface-700 rounded-xl
                    px-4 py-3 text-sm text-white placeholder-gray-500
                    resize-y transition-all duration-200
                    focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
                    ${expanded ? 'min-h-[300px] max-h-[50vh]' : 'min-h-[160px] max-h-[40vh]'}
                  `}
                />
              )}
            </div>

            {/* QA / Testing Details */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                QA / Testing Details
                <span className="text-xs text-gray-500 ml-2 font-normal">(optional)</span>
              </label>
              <textarea
                value={qaDetails}
                onChange={e => setQaDetails(e.target.value)}
                placeholder="How to verify this task... (e.g., test URLs, expected behavior, manual checks)"
                rows={3}
                className="
                  w-full bg-surface-850 border border-surface-700 rounded-xl
                  px-4 py-3 text-sm text-white placeholder-gray-500
                  resize-y transition-all duration-200
                  focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
                  min-h-[80px] max-h-[200px]
                "
              />
            </div>

            {/* Attach Documents */}
            {availableDocs.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Attach Documents
                  <span className="text-xs text-gray-500 ml-2 font-normal">(optional)</span>
                  {selectedDocIds.size > 0 && (
                    <span className="text-xs text-blue-400 ml-2 font-normal">{selectedDocIds.size} selected</span>
                  )}
                </label>
                <div className="bg-surface-850 border border-surface-700 rounded-xl max-h-40 overflow-y-auto">
                  {[...docsByFolder.entries()].map(([folder, docs]) => (
                    <div key={folder}>
                      <div className="px-3 py-1.5 text-[10px] text-gray-500 uppercase tracking-wider font-semibold bg-surface-800/50 sticky top-0 flex items-center gap-1.5">
                        <FileText className="w-3 h-3" />
                        {folder}
                      </div>
                      {docs.map(doc => (
                        <label
                          key={doc.id}
                          className="flex items-center gap-2.5 px-3 py-1.5 hover:bg-surface-800/50 cursor-pointer transition-colors"
                        >
                          <input
                            type="checkbox"
                            checked={selectedDocIds.has(doc.id)}
                            onChange={() => toggleDocSelection(doc.id)}
                            className="rounded border-surface-600 bg-surface-800 text-blue-500 focus:ring-blue-500/20 focus:ring-offset-0"
                          />
                          <span className="text-sm text-gray-300 truncate">{doc.title}</span>
                        </label>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Attach Images */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Attach Images
                <span className="text-xs text-gray-500 ml-2 font-normal">(optional)</span>
                {pendingImages.length > 0 && (
                  <span className="text-xs text-violet-400 ml-2 font-normal">{pendingImages.length} selected</span>
                )}
              </label>
              {pendingImages.length > 0 && (
                <div className="grid grid-cols-4 gap-2 mb-2">
                  {pendingImages.map((file, i) => (
                    <div key={i} className="group relative rounded-lg overflow-hidden border border-surface-700/50 bg-surface-850">
                      <img
                        src={URL.createObjectURL(file)}
                        alt={file.name}
                        className="w-full h-16 object-cover cursor-pointer"
                        onClick={() => setPreviewImage(URL.createObjectURL(file))}
                      />
                      <div className="px-1.5 py-0.5">
                        <p className="text-[10px] text-gray-400 truncate" title={file.name}>{file.name}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => removePendingImage(i)}
                        className="absolute top-1 right-1 p-0.5 rounded-md bg-black/60 text-gray-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <div className="relative">
                <div className="flex items-center gap-2 px-3 py-2 text-sm text-violet-400 bg-surface-850 border border-surface-700 border-dashed rounded-xl hover:border-violet-500/40 hover:bg-violet-500/5 transition-colors w-full justify-center pointer-events-none">
                  <ImagePlus className="w-4 h-4" />
                  Add Images
                </div>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
                  multiple
                  onChange={handleAddImages}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
            </div>

            {/* Resume Session Picker */}
            {tasksWithSessions.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Resume Session
                  <span className="text-xs text-gray-500 ml-2 font-normal">(optional)</span>
                </label>
                <div className="relative" ref={dropdownRef}>
                  <button
                    type="button"
                    onClick={() => setSessionDropdownOpen(!sessionDropdownOpen)}
                    className={`
                      w-full flex items-center justify-between gap-2
                      bg-surface-850 border rounded-xl px-4 py-3 text-sm
                      transition-all duration-200
                      ${resumeSessionId
                        ? 'border-accent-500/40 text-white'
                        : 'border-surface-700 text-gray-500'
                      }
                      hover:border-surface-600
                    `}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <GitBranch className={`w-4 h-4 flex-shrink-0 ${resumeSessionId ? 'text-accent-400' : 'text-gray-500'}`} />
                      {selectedSession ? (
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="truncate">{selectedSession.title}</span>
                          <span className={`text-[11px] flex-shrink-0 ${statusColor[selectedSession.status] || 'text-gray-400'}`}>
                            {selectedSession.status}
                          </span>
                          <span className="text-[11px] text-gray-600 flex-shrink-0">
                            {formatTimeAgo(selectedSession.updated_at)}
                          </span>
                        </div>
                      ) : (
                        <span>New session (default)</span>
                      )}
                    </div>
                    <ChevronDown className={`w-4 h-4 flex-shrink-0 text-gray-500 transition-transform ${sessionDropdownOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {sessionDropdownOpen && (
                    <div className="absolute z-20 mt-1 w-full bg-surface-850 border border-surface-700 rounded-xl shadow-modal overflow-hidden animate-fade-in-down">
                      <div className="max-h-48 overflow-y-auto">
                        <button
                          type="button"
                          onClick={() => { setResumeSessionId(null); setSessionDropdownOpen(false) }}
                          className={`
                            w-full text-left px-4 py-2.5 text-sm flex items-center gap-2
                            transition-colors hover:bg-surface-800
                            ${!resumeSessionId ? 'text-accent-400 bg-accent-500/5' : 'text-gray-300'}
                          `}
                        >
                          <Plus className="w-3.5 h-3.5 flex-shrink-0" />
                          New session
                        </button>
                        {tasksWithSessions.map(t => (
                          <button
                            type="button"
                            key={t.id}
                            onClick={() => { setResumeSessionId(t.claude_session_id); setSessionDropdownOpen(false) }}
                            className={`
                              w-full text-left px-4 py-2.5 text-sm
                              transition-colors hover:bg-surface-800
                              ${resumeSessionId === t.claude_session_id ? 'text-accent-400 bg-accent-500/5' : 'text-gray-300'}
                            `}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="truncate">{t.title}</span>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <span className={`text-[11px] ${statusColor[t.status] || 'text-gray-400'}`}>
                                  {t.status}
                                </span>
                                <span className="text-[11px] text-gray-600">
                                  {formatTimeAgo(t.updated_at)}
                                </span>
                              </div>
                            </div>
                            {t.assigned_agent && (
                              <span className="text-[11px] text-gray-500 mt-0.5 block">{t.assigned_agent}</span>
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                {resumeSessionId && (
                  <p className="mt-1.5 text-[11px] text-amber-400/70 flex items-center gap-1">
                    This task will continue in the session from "{selectedSession?.title}"
                  </p>
                )}
              </div>
            )}

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

      {/* Image preview lightbox */}
      {previewImage && (
        <div
          className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-8 animate-fade-in"
          onClick={e => { e.stopPropagation(); setPreviewImage(null) }}
        >
          <button
            className="absolute top-4 right-4 p-2 rounded-lg bg-black/50 text-gray-300 hover:text-white transition-colors"
            onClick={() => setPreviewImage(null)}
          >
            <X className="w-5 h-5" />
          </button>
          <img
            src={previewImage}
            alt="Preview"
            className="max-w-full max-h-full object-contain rounded-lg"
            onClick={e => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  )
}
