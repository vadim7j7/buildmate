import { KanbanBoard } from './components/KanbanBoard'
import { StatsBar } from './components/StatsBar'
import { TaskDetailPanel } from './components/TaskDetailPanel'
import { DashboardProvider, useDashboard } from './context/DashboardContext'

function DashboardLayout() {
  const { state } = useDashboard()

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-gray-100">
      <StatsBar />
      <div className="flex flex-1 overflow-hidden">
        <KanbanBoard />
        {state.selectedTaskId && <TaskDetailPanel />}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <DashboardProvider>
      <DashboardLayout />
    </DashboardProvider>
  )
}
