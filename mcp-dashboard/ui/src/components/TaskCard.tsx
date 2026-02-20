import { AlertCircle, CheckCircle, Circle, Loader, MessageSquare, XCircle } from 'lucide-react'
import type { Task, TaskStatus } from '../types'
import { AgentBadge } from './AgentBadge'

const STATUS_CONFIG: Record<TaskStatus, { icon: React.ReactNode; border: string }> = {
  pending: { icon: <Circle className="w-4 h-4 text-gray-400" />, border: 'border-gray-700' },
  in_progress: { icon: <Loader className="w-4 h-4 text-yellow-400 animate-spin" />, border: 'border-yellow-500/50' },
  completed: { icon: <CheckCircle className="w-4 h-4 text-green-400" />, border: 'border-green-500/50' },
  failed: { icon: <XCircle className="w-4 h-4 text-red-400" />, border: 'border-red-500/50' },
  blocked: { icon: <AlertCircle className="w-4 h-4 text-orange-400" />, border: 'border-orange-500/50' },
}

interface Props {
  task: Task
  selected: boolean
  onClick: () => void
}

export function TaskCard({ task, selected, onClick }: Props) {
  const config = STATUS_CONFIG[task.status]

  return (
    <div
      onClick={onClick}
      className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-gray-800/50 ${config.border} ${selected ? 'bg-gray-800 ring-1 ring-blue-500/50' : 'bg-gray-900/50'}`}
    >
      <div className="flex items-start gap-2 mb-2">
        <div className="mt-0.5 shrink-0">{config.icon}</div>
        <h3 className="text-sm font-medium text-gray-100 line-clamp-2 flex-1">{task.title}</h3>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <AgentBadge agent={task.assigned_agent} />

        {task.phase && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-300 uppercase tracking-wide">
            {task.phase}
          </span>
        )}

        {task.pending_questions > 0 && (
          <span className="flex items-center gap-0.5 text-amber-400">
            <MessageSquare className="w-3 h-3" />
            <span className="text-[10px]">{task.pending_questions}</span>
          </span>
        )}

        {task.source === 'dashboard' && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/50 text-blue-300">UI</span>
        )}
      </div>

      {/* Subtask progress bar */}
      {task.children.length > 0 && <SubtaskProgress children={task.children} />}
    </div>
  )
}

function SubtaskProgress({ children }: { children: Task[] }) {
  const total = children.length
  const counts = {
    completed: children.filter(c => c.status === 'completed').length,
    in_progress: children.filter(c => c.status === 'in_progress').length,
    failed: children.filter(c => c.status === 'failed').length,
    pending: children.filter(c => c.status === 'pending' || c.status === 'blocked').length,
  }

  return (
    <div className="mt-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-gray-500">
          {counts.completed}/{total} subtasks
        </span>
      </div>
      <div className="flex h-1.5 rounded-full overflow-hidden bg-gray-800 gap-px">
        {counts.completed > 0 && (
          <div className="bg-green-500 rounded-full" style={{ width: `${(counts.completed / total) * 100}%` }} />
        )}
        {counts.in_progress > 0 && (
          <div className="bg-yellow-500 rounded-full" style={{ width: `${(counts.in_progress / total) * 100}%` }} />
        )}
        {counts.failed > 0 && (
          <div className="bg-red-500 rounded-full" style={{ width: `${(counts.failed / total) * 100}%` }} />
        )}
        {counts.pending > 0 && (
          <div className="bg-gray-600 rounded-full" style={{ width: `${(counts.pending / total) * 100}%` }} />
        )}
      </div>
    </div>
  )
}
