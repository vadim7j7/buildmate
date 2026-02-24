import {
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Circle,
  Loader,
  MessageSquare,
  Play,
  Square,
  Trash2,
  X,
  XCircle,
} from 'lucide-react'
import { useState } from 'react'
import { api } from '../api/client'
import { useDashboard } from '../context/DashboardContext'
import type { Artifact, Question, Task, TaskStatus } from '../types'
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

export function TaskDetailPanel() {
  const { state, selectTask, refreshTasks, refreshStats } = useDashboard()
  const [answeringQuestion, setAnsweringQuestion] = useState<Question | null>(null)
  const [viewingArtifact, setViewingArtifact] = useState<Artifact | null>(null)

  const [subtasksOpen, setSubtasksOpen] = useState(true)
  const [artifactsOpen, setArtifactsOpen] = useState(false)
  const [activityOpen, setActivityOpen] = useState(false)

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

  return (
    <>
      <div className="w-[420px] bg-surface-900/95 backdrop-blur-md border-l border-surface-800/50 flex flex-col overflow-hidden animate-slide-in-right">
        {/* Header */}
        <div className="p-5 border-b border-surface-800/50">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="p-2 rounded-lg bg-surface-800">
                {STATUS_ICON[task.status]}
              </div>
              <h2 className="text-base font-semibold text-white truncate">{task.title}</h2>
            </div>
            <button
              onClick={() => selectTask(null)}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {task.description && (
            <p className="text-sm text-gray-400 mb-3 leading-relaxed">{task.description}</p>
          )}

          <div className="flex items-center gap-2 flex-wrap">
            <AgentBadge agent={task.assigned_agent} />
            {task.phase && (
              <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-purple-500/15 text-purple-300 text-[11px] font-medium uppercase tracking-wide border border-purple-500/20">
                {task.phase}
              </span>
            )}
            <span className="text-[11px] text-gray-600 font-mono">ID: {task.id}</span>
          </div>

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
            <div className="mt-4 p-4 bg-surface-850 rounded-xl text-sm text-gray-300 max-h-24 overflow-y-auto border border-surface-700/50">
              {task.result}
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
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto">
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
                        flex items-center gap-3 py-2.5 px-3 rounded-lg
                        bg-surface-850/50 hover:bg-surface-800/50
                        transition-colors
                      "
                    >
                      {STATUS_ICON[child.status]}
                      <span className="text-sm text-gray-300 flex-1 truncate">{child.title}</span>
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
    </>
  )
}
