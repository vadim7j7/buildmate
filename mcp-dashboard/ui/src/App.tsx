import { useEffect, useRef, useState } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { KanbanBoard } from './components/KanbanBoard'
import { ServicesPanel } from './components/ServicesPanel'
import { StatsBar } from './components/StatsBar'
import { TaskDetailPanel } from './components/TaskDetailPanel'
import { TeamPanel } from './components/TeamPanel'
import { ToastContainer } from './components/ToastContainer'
import { ChatProvider, useChat } from './context/ChatContext'
import { DashboardProvider, useDashboard } from './context/DashboardContext'

type PanelKey = 'chat' | 'team' | 'services'

function RightPanelStack() {
  const { state } = useDashboard()
  const { state: chatState } = useChat()

  // Stack tracks the z-order: last element = top
  const [stack, setStack] = useState<PanelKey[]>([])
  const prevOpen = useRef<Record<PanelKey, boolean>>({ chat: false, team: false, services: false })

  useEffect(() => {
    const current: Record<PanelKey, boolean> = {
      chat: chatState.chatOpen,
      team: state.showTeam,
      services: state.showServices,
    }

    const prev = prevOpen.current
    setStack(s => {
      let next = [...s]
      for (const key of ['chat', 'team', 'services'] as PanelKey[]) {
        if (current[key] && !prev[key]) {
          // Toggled on — move to top
          next = next.filter(k => k !== key)
          next.push(key)
        } else if (!current[key] && prev[key]) {
          // Toggled off — remove
          next = next.filter(k => k !== key)
        }
      }
      return next
    })

    prevOpen.current = current
  }, [chatState.chatOpen, state.showTeam, state.showServices])

  // No sidebar panels open — fall back to task detail
  if (stack.length === 0) {
    return state.selectedTaskId ? <TaskDetailPanel /> : null
  }

  return (
    <div className="relative w-[420px] flex-shrink-0">
      {stack.map((key, i) => (
        <div key={key} className="absolute inset-0" style={{ zIndex: i + 1 }}>
          {key === 'chat' && <ChatPanel />}
          {key === 'team' && <TeamPanel />}
          {key === 'services' && <ServicesPanel />}
        </div>
      ))}
    </div>
  )
}

function DashboardLayout() {
  const { toasts, dismissToast } = useDashboard()

  return (
    <div className="h-screen flex flex-col bg-surface-950 text-gray-100 overflow-hidden">
      {/* Header with gradient border */}
      <StatsBar />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Kanban Board */}
        <KanbanBoard />

        {/* Right Panel Stack */}
        <RightPanelStack />
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
