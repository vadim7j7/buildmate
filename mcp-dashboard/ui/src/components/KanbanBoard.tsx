import { Plus } from 'lucide-react'
import { useState } from 'react'
import { useDashboard } from '../context/DashboardContext'
import type { Task, TaskStatus } from '../types'
import { CreateTaskModal } from './CreateTaskModal'
import { TaskCard } from './TaskCard'

const COLUMNS: { status: TaskStatus; label: string; color: string }[] = [
  { status: 'pending', label: 'Pending', color: 'border-gray-600' },
  { status: 'in_progress', label: 'In Progress', color: 'border-yellow-500' },
  { status: 'completed', label: 'Completed', color: 'border-green-500' },
  { status: 'failed', label: 'Failed', color: 'border-red-500' },
  { status: 'blocked', label: 'Blocked', color: 'border-orange-500' },
]

export function KanbanBoard() {
  const { state, selectTask } = useDashboard()
  const [showCreate, setShowCreate] = useState(false)

  const tasksByStatus = (status: TaskStatus): Task[] =>
    state.tasks.filter(t => t.status === status)

  return (
    <>
      <div className="flex-1 overflow-x-auto p-4">
        <div className="flex gap-4 h-full min-w-max">
          {COLUMNS.map(col => (
            <div key={col.status} className="w-72 flex flex-col shrink-0">
              <div className={`flex items-center justify-between mb-3 pb-2 border-b-2 ${col.color}`}>
                <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                  {col.label}
                </h2>
                <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
                  {tasksByStatus(col.status).length}
                </span>
              </div>

              <div className="flex-1 space-y-2 overflow-y-auto pb-4">
                {col.status === 'pending' && (
                  <button
                    onClick={() => setShowCreate(true)}
                    className="w-full p-3 rounded-lg border border-dashed border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-500 transition-colors flex items-center justify-center gap-2 text-sm"
                  >
                    <Plus className="w-4 h-4" />
                    New Task
                  </button>
                )}

                {tasksByStatus(col.status).map(task => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    selected={state.selectedTaskId === task.id}
                    onClick={() => selectTask(task.id)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {showCreate && <CreateTaskModal onClose={() => setShowCreate(false)} />}
    </>
  )
}
