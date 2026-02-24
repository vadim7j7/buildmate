import { Plus } from 'lucide-react'
import { useState } from 'react'
import { useDashboard } from '../context/DashboardContext'
import type { Task, TaskStatus } from '../types'
import { CreateTaskModal } from './CreateTaskModal'
import { TaskCard } from './TaskCard'

type ColumnConfig = {
  status: TaskStatus
  label: string
  borderColor: string
  headerBg: string
  countBg: string
}

const COLUMNS: ColumnConfig[] = [
  {
    status: 'pending',
    label: 'Pending',
    borderColor: 'border-gray-600/50',
    headerBg: 'bg-surface-800/50',
    countBg: 'bg-surface-700',
  },
  {
    status: 'in_progress',
    label: 'In Progress',
    borderColor: 'border-amber-500/30',
    headerBg: 'bg-amber-500/10',
    countBg: 'bg-amber-500/20',
  },
  {
    status: 'completed',
    label: 'Completed',
    borderColor: 'border-emerald-500/30',
    headerBg: 'bg-emerald-500/10',
    countBg: 'bg-emerald-500/20',
  },
  {
    status: 'failed',
    label: 'Failed',
    borderColor: 'border-red-500/30',
    headerBg: 'bg-red-500/10',
    countBg: 'bg-red-500/20',
  },
  {
    status: 'blocked',
    label: 'Blocked',
    borderColor: 'border-orange-500/30',
    headerBg: 'bg-orange-500/10',
    countBg: 'bg-orange-500/20',
  },
]

export function KanbanBoard() {
  const { state, selectTask } = useDashboard()
  const [showCreate, setShowCreate] = useState(false)

  const tasksByStatus = (status: TaskStatus): Task[] =>
    state.tasks.filter(t => t.status === status)

  return (
    <>
      <div className="flex-1 overflow-x-auto p-6">
        <div className="flex gap-5 h-full min-w-max">
          {COLUMNS.map((col, index) => (
            <div
              key={col.status}
              className="w-80 flex flex-col shrink-0 animate-fade-in-up"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Column Header */}
              <div
                className={`
                  flex items-center justify-between mb-4 pb-3
                  border-b-2 ${col.borderColor}
                `}
              >
                <div className={`flex items-center gap-3 px-3 py-1.5 rounded-lg ${col.headerBg}`}>
                  <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">
                    {col.label}
                  </h2>
                  <span
                    className={`
                      text-xs font-semibold px-2 py-0.5 rounded-md
                      ${col.countBg} text-gray-200
                    `}
                  >
                    {tasksByStatus(col.status).length}
                  </span>
                </div>
              </div>

              {/* Column Content */}
              <div className="flex-1 space-y-3 overflow-y-auto pb-4 pr-1">
                {/* Add Task Button - Only in Pending */}
                {col.status === 'pending' && (
                  <button
                    onClick={() => setShowCreate(true)}
                    className="
                      group w-full p-4 rounded-xl
                      border-2 border-dashed border-surface-700
                      bg-surface-900/30 backdrop-blur-sm
                      text-gray-500 hover:text-gray-300
                      hover:border-accent-500/50 hover:bg-accent-500/5
                      transition-all duration-200
                      flex items-center justify-center gap-2
                    "
                  >
                    <div className="w-8 h-8 rounded-lg bg-surface-800 group-hover:bg-accent-500/20 flex items-center justify-center transition-colors">
                      <Plus className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-medium">New Task</span>
                  </button>
                )}

                {/* Task Cards */}
                {tasksByStatus(col.status).map((task, taskIndex) => (
                  <div
                    key={task.id}
                    className="animate-fade-in"
                    style={{ animationDelay: `${(index * 50) + (taskIndex * 30)}ms` }}
                  >
                    <TaskCard
                      task={task}
                      selected={state.selectedTaskId === task.id}
                      onClick={() => selectTask(task.id)}
                    />
                  </div>
                ))}

                {/* Empty State */}
                {tasksByStatus(col.status).length === 0 && col.status !== 'pending' && (
                  <div className="py-10 text-center">
                    <p className="text-sm text-gray-600">No tasks</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {showCreate && <CreateTaskModal onClose={() => setShowCreate(false)} />}
    </>
  )
}
