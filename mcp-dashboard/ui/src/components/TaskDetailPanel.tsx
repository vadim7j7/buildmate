import {
  AlertCircle,
  Check,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Circle,
  Clock,
  Coins,
  Expand,
  ExternalLink,
  FileText,
  GitBranch,
  ImagePlus,
  Loader,
  MessageSquare,
  Pencil,
  Play,
  RotateCcw,
  Save,
  Send,
  Square,
  Trash2,
  X,
  XCircle,
  Zap,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'
import { useDashboard } from '../context/DashboardContext'
import { useResizablePanel } from '../hooks/useResizablePanel'
import type { Artifact, Question, Task, TaskImage, TaskRevision, TaskStatus } from '../types'
import { ResizeHandle } from './ResizeHandle'
import { ActivityFeed } from './ActivityFeed'
import { AgentBadge } from './AgentBadge'
import { ArtifactItem } from './ArtifactItem'
import { ArtifactModal } from './ArtifactModal'
import { QuestionModal } from './QuestionModal'

const STATUS_ICON: Record<TaskStatus, React.ReactNode> = {
  pending: <Circle className="w-4 h-4 text-gray-400" />,
  in_progress: <Loader className="w-4 h-4 text-amber-400 animate-spin" />,
  completed: <CheckCircle className="w-4 h-4 text-emerald-400" />,
  failed: <XCircle className="w-4 h-4 text-red-400" />,
  blocked: <AlertCircle className="w-4 h-4 text-orange-400" />,
}

type SectionHeaderProps = {
  label: string
  count?: number
  expanded: boolean
  onToggle: () => void
}

function SectionHeader({ label, count, expanded, onToggle }: SectionHeaderProps) {
  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center gap-2 text-left group py-1"
    >
      <div className="w-5 h-5 rounded-md bg-surface-800 flex items-center justify-center group-hover:bg-surface-700 transition-colors">
        {expanded
          ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
          : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
        }
      </div>
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider group-hover:text-gray-300 transition-colors">
        {label}
      </h3>
      {count != null && (
        <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-surface-800 text-gray-500">
          {count}
        </span>
      )}
    </button>
  )
}

type FullViewModalProps = {
  title: string
  content: string
  onClose: () => void
}

function FullViewModal({ title, content, onClose }: FullViewModalProps) {
  return (
    <div
      className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm flex items-center justify-center p-6 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-surface-900 border border-surface-700/50 rounded-2xl shadow-modal w-full max-w-3xl max-h-[85vh] flex flex-col animate-scale-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-800/50">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <div className="artifact-markdown">
            <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
          </div>
        </div>
      </div>
    </div>
  )
}

type ExpandableTextProps = {
  content: string
  label: string
  maxLines?: number
}

function ExpandableText({ content, label, maxLines = 3 }: ExpandableTextProps) {
  const [clamped, setClamped] = useState(true)
  const [isOverflowing, setIsOverflowing] = useState(false)
  const [fullView, setFullView] = useState(false)
  const textRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = textRef.current
    if (el) {
      setIsOverflowing(el.scrollHeight > el.clientHeight + 1)
    }
  }, [content])

  return (
    <>
      <div className="relative mb-3 group/expandable">
        <div
          ref={textRef}
          className="text-sm text-gray-400 leading-relaxed artifact-markdown"
          style={clamped ? {
            display: '-webkit-box',
            WebkitLineClamp: maxLines,
            WebkitBoxOrient: 'vertical' as const,
            overflow: 'hidden',
          } : undefined}
        >
          <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
        </div>
        {(isOverflowing || !clamped) && (
          <div className="flex items-center gap-2 mt-1.5">
            <button
              onClick={() => setClamped(!clamped)}
              className="text-xs text-accent-400 hover:text-accent-300 font-medium transition-colors"
            >
              {clamped ? 'Show more' : 'Show less'}
            </button>
            <button
              onClick={() => setFullView(true)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              <Expand className="w-3 h-3" />
              Full view
            </button>
          </div>
        )}
      </div>
      {fullView && (
        <FullViewModal
          title={label}
          content={content}
          onClose={() => setFullView(false)}
        />
      )}
    </>
  )
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}

function formatDuration(ms: number): string {
  const secs = Math.floor(ms / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  const remainSecs = secs % 60
  if (mins < 60) return `${mins}m ${remainSecs}s`
  const hrs = Math.floor(mins / 60)
  const remainMins = mins % 60
  return `${hrs}h ${remainMins}m`
}

export function TaskDetailPanel() {
  const { state, selectTask, refreshTasks, refreshStats } = useDashboard()
  const [answeringQuestion, setAnsweringQuestion] = useState<Question | null>(null)
  const [viewingArtifact, setViewingArtifact] = useState<Artifact | null>(null)

  const [subtasksOpen, setSubtasksOpen] = useState(true)
  const [artifactsOpen, setArtifactsOpen] = useState(false)
  const [activityOpen, setActivityOpen] = useState(false)

  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [feedbackText, setFeedbackText] = useState('')
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false)
  const [revisions, setRevisions] = useState<TaskRevision[]>([])
  const [revisionsOpen, setRevisionsOpen] = useState(false)
  const [showSaveToDocs, setShowSaveToDocs] = useState(false)
  const [saveFolder, setSaveFolder] = useState('')
  const [isSavingDoc, setIsSavingDoc] = useState(false)

  // Inline editing state for pending tasks
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editQaDetails, setEditQaDetails] = useState('')
  const [isSavingEdit, setIsSavingEdit] = useState(false)

  // Task images state
  const [taskImages, setTaskImages] = useState<TaskImage[]>([])
  const [imagesOpen, setImagesOpen] = useState(false)
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [isUploadingImage, setIsUploadingImage] = useState(false)


  // Reset feedback form when switching tasks
  useEffect(() => {
    setShowFeedbackForm(false)
    setFeedbackText('')
    setIsSubmittingFeedback(false)
    setRevisions([])
    setRevisionsOpen(false)
    setShowSaveToDocs(false)
    setSaveFolder('')
    setIsEditing(false)
    setTaskImages([])
    setImagesOpen(false)
  }, [state.selectedTaskId])

  // Fetch revisions when task has revision_count > 0
  useEffect(() => {
    if (!state.selectedTaskId) return
    const task = state.tasks.find(t => t.id === state.selectedTaskId)
    if (!task || (task.revision_count || 0) === 0) {
      setRevisions([])
      return
    }
    api.getTaskRevisions(task.id).then(setRevisions).catch(() => setRevisions([]))
  }, [state.selectedTaskId, state.tasks])

  // Fetch task images
  useEffect(() => {
    if (!state.selectedTaskId) return
    api.listTaskImages(state.selectedTaskId).then(setTaskImages).catch(() => setTaskImages([]))
  }, [state.selectedTaskId])

  const task = state.tasks.find(t => t.id === state.selectedTaskId)
  if (!task) return null

  const pendingQuestions = state.selectedQuestions.filter(q => q.answer === null)
  const processStatus = state.processes[task.id]

  const handleRun = async () => {
    try {
      await api.runTask(task.id)
      await refreshTasks()
    } catch (err) {
      console.error('Failed to run task:', err)
    }
  }

  const handleCancel = async () => {
    try {
      await api.cancelTask(task.id)
      await refreshTasks()
    } catch (err) {
      console.error('Failed to cancel task:', err)
    }
  }

  const handleDelete = async () => {
    try {
      await api.deleteTask(task.id)
      selectTask(null)
      await refreshTasks()
      await refreshStats()
    } catch (err) {
      console.error('Failed to delete task:', err)
    }
  }

  const handleRequestChanges = async () => {
    if (!feedbackText.trim()) return
    setIsSubmittingFeedback(true)
    try {
      await api.requestChanges(task.id, feedbackText.trim())
      setShowFeedbackForm(false)
      setFeedbackText('')
      await refreshTasks()
    } catch (err) {
      console.error('Failed to request changes:', err)
    } finally {
      setIsSubmittingFeedback(false)
    }
  }

  const handleSaveToDocs = async () => {
    if (!task.result) return
    setIsSavingDoc(true)
    try {
      await api.saveFromTask(task.id, task.title, task.result, saveFolder.trim())
      setShowSaveToDocs(false)
      setSaveFolder('')
    } catch (err) {
      console.error('Failed to save to docs:', err)
    } finally {
      setIsSavingDoc(false)
    }
  }

  const handleStartEdit = () => {
    setEditTitle(task.title)
    setEditDescription(task.description || '')
    setEditQaDetails(task.qa_details || '')
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditTitle('')
    setEditDescription('')
    setEditQaDetails('')
  }

  const handleSaveEdit = async () => {
    if (!editTitle.trim()) return
    setIsSavingEdit(true)
    try {
      const updates: { title?: string; description?: string; qa_details?: string } = {}
      if (editTitle.trim() !== task.title) updates.title = editTitle.trim()
      if (editDescription !== (task.description || '')) updates.description = editDescription
      if (editQaDetails !== (task.qa_details || '')) updates.qa_details = editQaDetails
      if (Object.keys(updates).length > 0) {
        await api.updateTask(task.id, updates)
        await refreshTasks()
      }
      setIsEditing(false)
    } catch (err) {
      console.error('Failed to save task edits:', err)
    } finally {
      setIsSavingEdit(false)
    }
  }

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    setIsUploadingImage(true)
    try {
      for (const file of Array.from(files)) {
        await api.uploadTaskImage(task.id, file)
      }
      const updated = await api.listTaskImages(task.id)
      setTaskImages(updated)
      setImagesOpen(true)
    } catch (err) {
      console.error('Failed to upload image:', err)
    } finally {
      setIsUploadingImage(false)
      // Reset file input so the same file can be selected again
      e.target.value = ''
    }
  }

  const handleDeleteImage = async (imageId: string) => {
    try {
      await api.deleteTaskImage(task.id, imageId)
      setTaskImages(prev => prev.filter(i => i.id !== imageId))
    } catch (err) {
      console.error('Failed to delete image:', err)
    }
  }

  const isPending = task.status === 'pending'

  const canRequestChanges = (task.status === 'completed' || task.status === 'failed') && !!task.claude_session_id

  const { panelWidth, handleResizeStart, MIN_WIDTH, MAX_WIDTH } = useResizablePanel('task')
  // TaskDetailPanel renders outside the stack, so it sets its own width via style

  return (
    <>
      <div
        className="bg-surface-900/95 backdrop-blur-md border-l border-surface-800/50 flex flex-col overflow-hidden animate-slide-in-right relative"
        style={{ width: panelWidth, minWidth: MIN_WIDTH, maxWidth: MAX_WIDTH }}
      >
        <ResizeHandle onMouseDown={handleResizeStart} />

        {/* Fixed title bar */}
        <div className="flex items-start justify-between p-5 pb-3 flex-shrink-0">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="p-2 rounded-lg bg-surface-800">
              {STATUS_ICON[task.status]}
            </div>
            {isEditing ? (
              <input
                value={editTitle}
                onChange={e => setEditTitle(e.target.value)}
                className="flex-1 bg-surface-800 text-base font-semibold text-white rounded-lg px-3 py-1.5 border border-surface-700 focus:border-accent-500/50 focus:outline-none"
                autoFocus
              />
            ) : (
              <h2 className="text-base font-semibold text-white truncate">{task.title}</h2>
            )}
          </div>
          <div className="flex items-center gap-1">
            {isPending && !isEditing && (
              <button
                onClick={handleStartEdit}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
                title="Edit task"
              >
                <Pencil className="w-4 h-4" />
              </button>
            )}
            {isEditing && (
              <>
                <button
                  onClick={handleSaveEdit}
                  disabled={!editTitle.trim() || isSavingEdit}
                  className="p-2 rounded-lg text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 transition-colors disabled:opacity-50"
                  title="Save changes"
                >
                  <Check className="w-4 h-4" />
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
                  title="Cancel editing"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            )}
            {!isEditing && (
              <button
                onClick={() => selectTask(null)}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Single scrollable area for everything */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-5 pb-5">
            {isEditing ? (
              <div className="mb-3">
                <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-1.5 block">
                  Description
                </label>
                <textarea
                  value={editDescription}
                  onChange={e => setEditDescription(e.target.value)}
                  placeholder="Task description (markdown supported)..."
                  className="
                    w-full bg-surface-800 text-sm text-gray-200 rounded-lg p-3
                    border border-surface-700 focus:border-accent-500/50 focus:outline-none
                    resize-none placeholder-gray-500
                  "
                  rows={6}
                />
                <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-1.5 block mt-3">
                  QA / Testing Details <span className="text-gray-600 normal-case tracking-normal font-normal">(optional)</span>
                </label>
                <textarea
                  value={editQaDetails}
                  onChange={e => setEditQaDetails(e.target.value)}
                  placeholder="How to verify this task... (e.g., test URLs, expected behavior)"
                  className="
                    w-full bg-surface-800 text-sm text-gray-200 rounded-lg p-3
                    border border-surface-700 focus:border-accent-500/50 focus:outline-none
                    resize-none placeholder-gray-500
                  "
                  rows={3}
                />
              </div>
            ) : (
              task.description && (
                <ExpandableText content={task.description} label="Description" />
              )
            )}

            {task.qa_details && (
              <div className="mt-3 p-3 bg-emerald-500/5 rounded-xl border border-emerald-500/20">
                <span className="text-[10px] text-emerald-400 uppercase tracking-wider font-semibold">QA / Testing Details</span>
                <ExpandableText content={task.qa_details} label="QA Details" maxLines={3} />
              </div>
            )}

            <div className="flex items-center gap-2 flex-wrap">
              <AgentBadge agent={task.assigned_agent} />
              {task.phase && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-purple-500/15 text-purple-300 text-[11px] font-medium uppercase tracking-wide border border-purple-500/20">
                  {task.phase}
                </span>
              )}
              <span className="text-[11px] text-gray-600 font-mono">ID: {task.id}</span>
              {task.revision_count > 0 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-400 text-[10px] font-medium border border-amber-500/20">
                  Rev {task.revision_count}
                </span>
              )}
            </div>

            {/* Branches & PRs */}
            {task.branches?.length > 0 && (
              <div className="mt-3 space-y-1.5">
                {task.branches.map(branch => (
                  <div
                    key={branch.id}
                    className="flex items-center gap-2 px-3 py-2 bg-surface-850 rounded-lg border border-surface-700/50"
                  >
                    <GitBranch className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                    <code className="text-xs text-cyan-300 font-mono truncate">{branch.branch_name}</code>
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-surface-700 text-[10px] text-gray-400 font-medium flex-shrink-0">
                      {branch.repo_name}
                    </span>
                    {branch.pr_url && (
                      <a
                        href={branch.pr_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-auto inline-flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300 transition-colors flex-shrink-0"
                      >
                        PR #{branch.pr_number}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Usage Stats */}
            {(task.input_tokens > 0 || task.output_tokens > 0 || task.cost_usd > 0) && (
              <div className="mt-4">
                {revisions.length > 0 && (
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-1.5">
                    Cumulative Totals
                  </div>
                )}
              </div>
            )}
            {(task.input_tokens > 0 || task.output_tokens > 0 || task.cost_usd > 0) && (
              <div className={`${revisions.length > 0 ? '' : 'mt-4'} grid grid-cols-2 gap-2`}>
                <div className="flex items-center gap-2 px-3 py-2 bg-surface-850 rounded-lg border border-surface-700/50">
                  <Zap className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">Tokens</div>
                    <div className="text-xs text-gray-300 font-medium">
                      {formatNumber(task.input_tokens + task.output_tokens)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-surface-850 rounded-lg border border-surface-700/50">
                  <Coins className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">Cost</div>
                    <div className="text-xs text-gray-300 font-medium">
                      ${task.cost_usd < 0.01 && task.cost_usd > 0 ? task.cost_usd.toFixed(4) : task.cost_usd.toFixed(2)}
                    </div>
                  </div>
                </div>
                {task.duration_ms > 0 && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-surface-850 rounded-lg border border-surface-700/50">
                    <Clock className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                    <div className="min-w-0">
                      <div className="text-[10px] text-gray-500 uppercase tracking-wider">Duration</div>
                      <div className="text-xs text-gray-300 font-medium">{formatDuration(task.duration_ms)}</div>
                    </div>
                  </div>
                )}
                {task.num_turns > 0 && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-surface-850 rounded-lg border border-surface-700/50">
                    <MessageSquare className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                    <div className="min-w-0">
                      <div className="text-[10px] text-gray-500 uppercase tracking-wider">Turns</div>
                      <div className="text-xs text-gray-300 font-medium">{task.num_turns}</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Process Status */}
            {processStatus?.status === 'running' && (
              <div className="mt-4 flex items-center gap-3 px-4 py-3 bg-accent-500/10 border border-accent-500/20 rounded-xl">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-accent-500" />
                </span>
                <span className="text-sm text-accent-300 font-medium">
                  Claude is running
                  {processStatus.pid && (
                    <span className="text-accent-400/60 ml-1.5 font-normal">(PID {processStatus.pid})</span>
                  )}
                </span>
              </div>
            )}

            {task.result && (
              <div className="mt-4 p-4 bg-surface-850 rounded-xl border border-surface-700/50">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Result</span>
                  <button
                    onClick={() => setShowSaveToDocs(!showSaveToDocs)}
                    className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] text-blue-400 hover:bg-blue-500/10 transition-colors"
                  >
                    <Save className="w-3 h-3" /> Save to Docs
                  </button>
                </div>
                {showSaveToDocs && (
                  <div className="mb-2 flex items-center gap-2 p-2 bg-surface-800 rounded-lg border border-surface-700/50">
                    <FileText className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                    <input
                      value={saveFolder}
                      onChange={e => setSaveFolder(e.target.value)}
                      placeholder="Folder (optional)"
                      className="flex-1 bg-transparent text-xs text-gray-200 placeholder-gray-500 outline-none"
                    />
                    <button
                      onClick={handleSaveToDocs}
                      disabled={isSavingDoc}
                      className="px-2 py-1 text-[11px] font-medium bg-blue-600 text-white rounded-md hover:bg-blue-500 transition-colors disabled:opacity-50"
                    >
                      {isSavingDoc ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                )}
                <ExpandableText content={task.result} label="Result" maxLines={4} />
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 mt-4">
              {task.source === 'dashboard' && task.status === 'pending' && (
                <button
                  onClick={handleRun}
                  className="
                    flex items-center gap-2 px-4 py-2.5 text-sm font-medium
                    bg-gradient-to-r from-emerald-600 to-emerald-500 text-white
                    rounded-xl shadow-[0_0_15px_-5px_rgba(16,185,129,0.3)]
                    hover:from-emerald-500 hover:to-emerald-400
                    transition-all duration-200 active:scale-[0.98]
                  "
                >
                  <Play className="w-4 h-4" /> Run Task
                </button>
              )}
              {task.status === 'in_progress' && (
                <button
                  onClick={handleCancel}
                  className="
                    flex items-center gap-2 px-4 py-2.5 text-sm font-medium
                    bg-red-600/80 hover:bg-red-500 text-white
                    rounded-xl transition-colors
                  "
                >
                  <Square className="w-4 h-4" /> Cancel
                </button>
              )}
              {canRequestChanges && (
                <button
                  onClick={() => setShowFeedbackForm(!showFeedbackForm)}
                  className="
                    flex items-center gap-2 px-4 py-2.5 text-sm font-medium
                    bg-amber-600/80 hover:bg-amber-500 text-white
                    rounded-xl transition-colors
                  "
                >
                  <RotateCcw className="w-4 h-4" /> Request Changes
                </button>
              )}
              {(task.status === 'completed' || task.status === 'failed' || task.status === 'pending') && (
                <button
                  onClick={handleDelete}
                  className="
                    flex items-center gap-2 px-4 py-2.5 text-sm font-medium
                    text-gray-400 hover:text-red-400
                    rounded-xl hover:bg-red-500/10
                    transition-all duration-200
                  "
                >
                  <Trash2 className="w-4 h-4" /> Delete
                </button>
              )}
            </div>

            {/* Feedback Form */}
            {showFeedbackForm && (
              <div className="mt-3 border border-amber-500/30 rounded-xl p-3 bg-amber-500/5">
                <textarea
                  value={feedbackText}
                  onChange={e => setFeedbackText(e.target.value)}
                  placeholder="Describe what changes you'd like..."
                  className="
                    w-full bg-surface-800 text-sm text-gray-200 rounded-lg p-3
                    border border-surface-700 focus:border-amber-500/50 focus:outline-none
                    resize-none placeholder-gray-500
                  "
                  rows={3}
                />
                <div className="flex gap-2 mt-2 justify-end">
                  <button
                    onClick={() => { setShowFeedbackForm(false); setFeedbackText('') }}
                    className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-gray-300 rounded-lg hover:bg-surface-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleRequestChanges}
                    disabled={!feedbackText.trim() || isSubmittingFeedback}
                    className="
                      flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium
                      bg-amber-600 hover:bg-amber-500 text-white
                      rounded-lg transition-colors
                      disabled:opacity-50 disabled:cursor-not-allowed
                    "
                  >
                    <Send className="w-3 h-3" />
                    {isSubmittingFeedback ? 'Submitting...' : 'Submit'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sections divider */}
          <div className="border-t border-surface-800/50" />

          {/* Task Images */}
          {(taskImages.length > 0 || isPending) && (
            <div className="p-5 border-b border-surface-800/50">
              <div className="flex items-center justify-between">
                <SectionHeader
                  label="Images"
                  count={taskImages.length || undefined}
                  expanded={imagesOpen}
                  onToggle={() => setImagesOpen(!imagesOpen)}
                />
                {isPending && (
                  <div className={`relative ${isUploadingImage ? 'opacity-50 pointer-events-none' : ''}`}>
                    <div className="flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-violet-400 hover:bg-violet-500/10 rounded-lg transition-colors pointer-events-none">
                      {isUploadingImage ? (
                        <Loader className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <ImagePlus className="w-3.5 h-3.5" />
                      )}
                      {isUploadingImage ? 'Uploading...' : 'Add'}
                    </div>
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
                      multiple
                      onChange={handleImageUpload}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </div>
                )}
              </div>
              {imagesOpen && taskImages.length > 0 && (
                <div className="grid grid-cols-3 gap-2 mt-3">
                  {taskImages.map(img => (
                    <div key={img.id} className="group relative rounded-lg overflow-hidden border border-surface-700/50 bg-surface-850">
                      <img
                        src={api.getImageUrl(img.filename)}
                        alt={img.original_name}
                        className="w-full h-20 object-cover cursor-pointer"
                        onClick={() => setPreviewImage(api.getImageUrl(img.filename))}
                      />
                      <div className="px-1.5 py-1">
                        <p className="text-[10px] text-gray-400 truncate" title={img.original_name}>
                          {img.original_name}
                        </p>
                      </div>
                      {isPending && (
                        <button
                          onClick={() => handleDeleteImage(img.id)}
                          className="absolute top-1 right-1 p-1 rounded-md bg-black/60 text-gray-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {imagesOpen && taskImages.length === 0 && isPending && (
                <p className="text-xs text-gray-500 mt-2">No images attached. Click Add to upload.</p>
              )}
            </div>
          )}

          {/* Pending Questions */}
          {pendingQuestions.length > 0 && (
            <div className="p-5 border-b border-surface-800/50">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1.5 rounded-lg bg-amber-500/15">
                  <MessageSquare className="w-4 h-4 text-amber-400" />
                </div>
                <h3 className="text-sm font-semibold text-amber-400">
                  Pending Questions ({pendingQuestions.length})
                </h3>
              </div>
              <div className="space-y-2">
                {pendingQuestions.map(q => (
                  <button
                    key={q.id}
                    onClick={() => setAnsweringQuestion(q)}
                    className="
                      w-full text-left p-4 rounded-xl
                      border border-amber-500/30 bg-amber-500/5
                      hover:bg-amber-500/10 hover:border-amber-500/40
                      transition-all duration-200
                    "
                  >
                    <p className="text-sm text-gray-200 line-clamp-2">{q.question}</p>
                    {q.agent && (
                      <p className="text-[11px] text-gray-500 mt-2">From: {q.agent}</p>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Subtasks */}
          {task.children.length > 0 && (
            <div className="p-5 border-b border-surface-800/50">
              <SectionHeader
                label="Subtasks"
                count={task.children.length}
                expanded={subtasksOpen}
                onToggle={() => setSubtasksOpen(!subtasksOpen)}
              />
              {subtasksOpen && (
                <div className="space-y-1.5 mt-3">
                  {task.children.map((child: Task) => (
                    <div
                      key={child.id}
                      className="
                        flex items-start gap-3 py-2.5 px-3 rounded-lg
                        bg-surface-850/50 hover:bg-surface-800/50
                        transition-colors
                      "
                    >
                      <div className="mt-0.5">{STATUS_ICON[child.status]}</div>
                      <div className="flex-1 min-w-0">
                        <span className="text-sm text-gray-300 block truncate">{child.title}</span>
                        {child.result && (
                          <p
                            title={child.result}
                            className="text-[11px] text-gray-500 mt-0.5 truncate"
                          >
                            {child.result}
                          </p>
                        )}
                      </div>
                      <AgentBadge agent={child.assigned_agent} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Artifacts */}
          {state.selectedArtifacts.length > 0 && (
            <div className="p-5 border-b border-surface-800/50">
              <SectionHeader
                label="Artifacts"
                count={state.selectedArtifacts.length}
                expanded={artifactsOpen}
                onToggle={() => setArtifactsOpen(!artifactsOpen)}
              />
              {artifactsOpen && (
                <div className="space-y-2 mt-3">
                  {state.selectedArtifacts.map(a => (
                    <ArtifactItem key={a.id} artifact={a} onClick={() => setViewingArtifact(a)} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Revision History */}
          {revisions.length > 0 && (
            <div className="p-5 border-b border-surface-800/50">
              <SectionHeader
                label="Revision History"
                count={revisions.length}
                expanded={revisionsOpen}
                onToggle={() => setRevisionsOpen(!revisionsOpen)}
              />
              {revisionsOpen && (
                <div className="space-y-2 mt-3">
                  {revisions.map(rev => (
                    <div
                      key={rev.id}
                      className="px-3 py-2.5 rounded-lg bg-surface-850/50 border border-surface-700/50"
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <GitBranch className="w-3.5 h-3.5 text-amber-400" />
                        <span className="text-xs font-medium text-gray-300">
                          Revision {rev.revision_number}
                        </span>
                        {rev.status && (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-medium ${
                            rev.status === 'completed'
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
                              : rev.status === 'failed'
                                ? 'bg-red-500/15 text-red-400 border border-red-500/20'
                                : 'bg-gray-500/15 text-gray-400 border border-gray-500/20'
                          }`}>
                            {rev.status}
                          </span>
                        )}
                      </div>
                      {rev.feedback && (
                        <p className="text-[11px] text-gray-500 mb-1.5 line-clamp-2" title={rev.feedback}>
                          {rev.feedback}
                        </p>
                      )}
                      <div className="flex items-center gap-3 text-[10px] text-gray-500">
                        {(rev.input_tokens > 0 || rev.output_tokens > 0) && (
                          <span className="flex items-center gap-1">
                            <Zap className="w-3 h-3 text-blue-400/60" />
                            {formatNumber(rev.input_tokens + rev.output_tokens)}
                          </span>
                        )}
                        {rev.cost_usd > 0 && (
                          <span className="flex items-center gap-1">
                            <Coins className="w-3 h-3 text-emerald-400/60" />
                            ${rev.cost_usd < 0.01 ? rev.cost_usd.toFixed(4) : rev.cost_usd.toFixed(2)}
                          </span>
                        )}
                        {rev.duration_ms > 0 && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-amber-400/60" />
                            {formatDuration(rev.duration_ms)}
                          </span>
                        )}
                        {rev.num_turns > 0 && (
                          <span className="flex items-center gap-1">
                            <MessageSquare className="w-3 h-3 text-purple-400/60" />
                            {rev.num_turns}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Activity Feed */}
          <div className="p-5">
            <SectionHeader
              label="Activity"
              expanded={activityOpen}
              onToggle={() => setActivityOpen(!activityOpen)}
            />
            {activityOpen && (
              <div className="mt-3">
                <ActivityFeed activity={state.selectedActivity} />
              </div>
            )}
          </div>
        </div>
      </div>

      {answeringQuestion && (
        <QuestionModal question={answeringQuestion} onClose={() => setAnsweringQuestion(null)} />
      )}

      {viewingArtifact && (
        <ArtifactModal artifact={viewingArtifact} onClose={() => setViewingArtifact(null)} />
      )}

      {/* Image preview lightbox */}
      {previewImage && (
        <div
          className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-8 animate-fade-in"
          onClick={() => setPreviewImage(null)}
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
    </>
  )
}
