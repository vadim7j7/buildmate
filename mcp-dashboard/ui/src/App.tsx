import { ChatPanel } from './components/ChatPanel'
import { KanbanBoard } from './components/KanbanBoard'
import { ServicesPanel } from './components/ServicesPanel'
import { StatsBar } from './components/StatsBar'
import { TaskDetailPanel } from './components/TaskDetailPanel'
import { ToastContainer } from './components/ToastContainer'
import { ChatProvider, useChat } from './context/ChatContext'
import { DashboardProvider, useDashboard } from './context/DashboardContext'

function DashboardLayout() {
  const { state, toasts, dismissToast } = useDashboard()
  const { state: chatState } = useChat()

  return (
    <div className="h-screen flex flex-col bg-surface-950 text-gray-100 overflow-hidden">
      {/* Header with gradient border */}
      <StatsBar />

      {/* Services Panel */}
      {state.showServices && <ServicesPanel />}

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Kanban Board */}
        <KanbanBoard />

        {/* Right Panel - Chat or Task Detail */}
        {chatState.chatOpen ? (
          <ChatPanel />
        ) : (
          state.selectedTaskId && <TaskDetailPanel />
        )}
      </div>

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}

export default function App() {
  return (
    <ChatProvider>
      <DashboardProvider>
        <DashboardLayout />
      </DashboardProvider>
    </ChatProvider>
  )
}
