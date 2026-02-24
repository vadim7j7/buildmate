import { AlertCircle, Award, CheckCircle, Circle, Loader, MessageSquare, XCircle } from 'lucide-react'
import type { Task, TaskStatus } from '../types'
import { AgentBadge } from './AgentBadge'

type StatusConfig = {
  icon: React.ReactNode
  border: string
  glow: string
  bg: string
}

const STATUS_CONFIG: Record<TaskStatus, StatusConfig> = {
  pending: {
    icon: <Circle className="w-4 h-4 text-gray-400" />,
    border: 'border-surface-700',
    glow: '',
    bg: 'bg-surface-900/60',
  },
  in_progress: {
    icon: <Loader className="w-4 h-4 text-amber-400 animate-spin" />,
    border: 'border-amber-500/40',
    glow: 'shadow-[0_0_15px_-5px_rgba(245,158,11,0.3)]',
    bg: 'bg-amber-500/5',
  },
  completed: {
    icon: <CheckCircle className="w-4 h-4 text-emerald-400" />,
    border: 'border-emerald-500/40',
    glow: '',
    bg: 'bg-emerald-500/5',
  },
  failed: {
    icon: <XCircle className="w-4 h-4 text-red-400" />,
    border: 'border-red-500/40',
    glow: '',
    bg: 'bg-red-500/5',
  },
  blocked: {
    icon: <AlertCircle className="w-4 h-4 text-orange-400" />,
    border: 'border-orange-500/40',
    glow: '',
    bg: 'bg-orange-500/5',
  },
}

type TaskCardProps = {
  task: Task
  selected: boolean
  onClick: () => void
}

export function TaskCard({ task, selected, onClick }: TaskCardProps) {
  const config = STATUS_CONFIG[task.status]

  return (
    <div
      onClick={onClick}
      className={`
        group relative p-4 rounded-xl border cursor-pointer
        backdrop-blur-sm transition-all duration-200
        ${config.border} ${config.bg} ${config.glow}
        ${selected
          ? 'bg-surface-800/80 ring-2 ring-accent-500/50 border-accent-500/30'
          : 'hover:bg-surface-850/80 hover:border-surface-600/50 hover:shadow-card'
        }
        active:scale-[0.99]
      `}
    >
      {/* Status indicator line */}
      {task.status === 'in_progress' && (
        <div className="absolute top-0 left-4 right-4 h-0.5 bg-gradient-to-r from-transparent via-amber-500/50 to-transparent rounded-full" />
      )}

      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="mt-0.5 shrink-0 transition-transform duration-200 group-hover:scale-110">
          {config.icon}
        </div>
        <h3 className="text-sm font-medium text-gray-100 line-clamp-2 flex-1 leading-snug">
          {task.title}
        </h3>
      </div>

      {/* Meta Row */}
      <div className="flex items-center gap-2 flex-wrap">
        <AgentBadge agent={task.assigned_agent} />

        {task.phase && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-300 text-[10px] font-medium uppercase tracking-wider border border-purple-500/20">
            {task.phase}
          </span>
        )}

        {task.pending_questions > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-400 border border-amber-500/20">
            <MessageSquare className="w-3 h-3" />
            <span className="text-[10px] font-medium">{task.pending_questions}</span>
          </span>
        )}

        {task.source === 'dashboard' && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-accent-500/15 text-accent-300 text-[10px] font-medium border border-accent-500/20">
            UI
          </span>
        )}
      </div>

      {/* Subtask Progress */}
      {task.children.length > 0 && <SubtaskProgress children={task.children} />}

      {/* Eval Score */}
      {task.eval_score != null && <EvalScoreBadge score={task.eval_score} grade={task.eval_grade} />}
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
    <div className="mt-3 pt-3 border-t border-surface-700/50">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] text-gray-500 font-medium">
          {counts.completed}/{total} subtasks
        </span>
        <span className="text-[10px] text-gray-600">
          {Math.round((counts.completed / total) * 100)}%
        </span>
      </div>
      <div className="flex h-1.5 rounded-full overflow-hidden bg-surface-800 gap-0.5">
        {counts.completed > 0 && (
          <div
            className="bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-500"
            style={{ width: `${(counts.completed / total) * 100}%` }}
          />
        )}
        {counts.in_progress > 0 && (
          <div
            className="bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all duration-500"
            style={{ width: `${(counts.in_progress / total) * 100}%` }}
          />
        )}
        {counts.failed > 0 && (
          <div
            className="bg-gradient-to-r from-red-500 to-red-400 rounded-full transition-all duration-500"
            style={{ width: `${(counts.failed / total) * 100}%` }}
          />
        )}
        {counts.pending > 0 && (
          <div
            className="bg-surface-600 rounded-full transition-all duration-500"
            style={{ width: `${(counts.pending / total) * 100}%` }}
          />
        )}
      </div>
    </div>
  )
}

function EvalScoreBadge({ score, grade }: { score: number; grade?: string | null }) {
  const pct = Math.round(score * 100)
  const isExcellent = pct >= 90
  const isGood = pct >= 70
  const colorClass = isExcellent ? 'text-emerald-400' : isGood ? 'text-amber-400' : 'text-red-400'
  const barColorClass = isExcellent
    ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
    : isGood
      ? 'bg-gradient-to-r from-amber-500 to-amber-400'
      : 'bg-gradient-to-r from-red-500 to-red-400'

  return (
    <div className="mt-3 pt-3 border-t border-surface-700/50">
      <div className="flex items-center gap-2">
        <Award className={`w-3.5 h-3.5 ${colorClass}`} />
        <span className={`text-[11px] font-semibold ${colorClass}`}>
          {grade || `${pct}%`}
        </span>
        <div className="flex-1 h-1.5 rounded-full bg-surface-800 overflow-hidden">
          <div
            className={`h-full rounded-full ${barColorClass} transition-all duration-500`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-[10px] text-gray-500 font-medium">eval</span>
      </div>
    </div>
  )
}
