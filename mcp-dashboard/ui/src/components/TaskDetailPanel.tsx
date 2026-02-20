import {
  AlertCircle,
  CheckCircle,
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
import type { Question, Task, TaskStatus } from '../types'
import { ActivityFeed } from './ActivityFeed'
import { AgentBadge } from './AgentBadge'
import { QuestionModal } from './QuestionModal'

const STATUS_ICON: Record<TaskStatus, React.ReactNode> = {
  pending: <Circle className="w-3.5 h-3.5 text-gray-400" />,
  in_progress: <Loader className="w-3.5 h-3.5 text-yellow-400 animate-spin" />,
  completed: <CheckCircle className="w-3.5 h-3.5 text-green-400" />,
  failed: <XCircle className="w-3.5 h-3.5 text-red-400" />,
  blocked: <AlertCircle className="w-3.5 h-3.5 text-orange-400" />,
}

export function TaskDetailPanel() {
  const { state, selectTask, refreshTasks, refreshStats } = useDashboard()
  const [answeringQuestion, setAnsweringQuestion] = useState<Question | null>(null)

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
      <div className="w-96 bg-gray-900 border-l border-gray-800 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              {STATUS_ICON[task.status]}
              <h2 className="text-sm font-semibold text-white truncate">{task.title}</h2>
            </div>
            <button onClick={() => selectTask(null)} className="text-gray-400 hover:text-white ml-2 shrink-0">
              <X className="w-4 h-4" />
            </button>
          </div>

          {task.description && (
            <p className="text-xs text-gray-400 mb-2">{task.description}</p>
          )}

          <div className="flex items-center gap-2 flex-wrap">
            <AgentBadge agent={task.assigned_agent} />
            {task.phase && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-900/50 text-purple-300 uppercase tracking-wide">
                {task.phase}
              </span>
            )}
            <span className="text-[10px] text-gray-600">ID: {task.id}</span>
          </div>

          {/* Process Status */}
          {processStatus?.status === 'running' && (
            <div className="mt-2 flex items-center gap-2 px-2.5 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500" />
              </span>
              <span className="text-xs text-blue-300">
                Claude is running
                {processStatus.pid && <span className="text-blue-400/60 ml-1">(PID {processStatus.pid})</span>}
              </span>
            </div>
          )}

          {task.result && (
            <div className="mt-2 p-2 bg-gray-800 rounded text-xs text-gray-300 max-h-20 overflow-y-auto">
              {task.result}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-3">
            {task.source === 'dashboard' && task.status === 'pending' && (
              <button
                onClick={handleRun}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors"
              >
                <Play className="w-3 h-3" /> Run
              </button>
            )}
            {task.status === 'in_progress' && (
              <button
                onClick={handleCancel}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-red-600/80 hover:bg-red-600 text-white rounded-lg transition-colors"
              >
                <Square className="w-3 h-3" /> Cancel
              </button>
            )}
            {(task.status === 'completed' || task.status === 'failed' || task.status === 'pending') && (
              <button
                onClick={handleDelete}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 hover:text-red-400 transition-colors"
              >
                <Trash2 className="w-3 h-3" /> Delete
              </button>
            )}
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          {/* Pending Questions */}
          {pendingQuestions.length > 0 && (
            <div className="p-4 border-b border-gray-800">
              <h3 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5" />
                Pending Questions ({pendingQuestions.length})
              </h3>
              <div className="space-y-2">
                {pendingQuestions.map(q => (
                  <button
                    key={q.id}
                    onClick={() => setAnsweringQuestion(q)}
                    className="w-full text-left p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/5 hover:bg-amber-500/10 transition-colors"
                  >
                    <p className="text-xs text-gray-200 line-clamp-2">{q.question}</p>
                    {q.agent && <p className="text-[10px] text-gray-500 mt-1">From: {q.agent}</p>}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Subtasks */}
          {task.children.length > 0 && (
            <div className="p-4 border-b border-gray-800">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                Subtasks ({task.children.length})
              </h3>
              <div className="space-y-1">
                {task.children.map((child: Task) => (
                  <div key={child.id} className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-gray-800/50">
                    {STATUS_ICON[child.status]}
                    <span className="text-xs text-gray-300 flex-1 truncate">{child.title}</span>
                    <AgentBadge agent={child.assigned_agent} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Activity Feed */}
          <div className="p-4">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              Activity
            </h3>
            <ActivityFeed activity={state.selectedActivity} />
          </div>
        </div>
      </div>

      {answeringQuestion && (
        <QuestionModal question={answeringQuestion} onClose={() => setAnsweringQuestion(null)} />
      )}
    </>
  )
}
