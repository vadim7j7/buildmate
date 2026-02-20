import { AlertCircle, ArrowRight, HelpCircle, MessageSquare, Plus } from 'lucide-react'
import type { Activity } from '../types'

const EVENT_ICONS: Record<string, React.ReactNode> = {
  created: <Plus className="w-3 h-3 text-blue-400" />,
  status_change: <ArrowRight className="w-3 h-3 text-yellow-400" />,
  phase_change: <ArrowRight className="w-3 h-3 text-purple-400" />,
  message: <MessageSquare className="w-3 h-3 text-gray-400" />,
  question: <HelpCircle className="w-3 h-3 text-amber-400" />,
  answer: <MessageSquare className="w-3 h-3 text-green-400" />,
  error: <AlertCircle className="w-3 h-3 text-red-400" />,
}

export function ActivityFeed({ activity }: { activity: Activity[] }) {
  if (activity.length === 0) {
    return <p className="text-sm text-gray-500 text-center py-4">No activity yet</p>
  }

  return (
    <div className="space-y-1.5 max-h-64 overflow-y-auto">
      {activity.map(item => (
        <div key={item.id} className="flex items-start gap-2 text-xs px-2 py-1.5 rounded hover:bg-gray-800/50">
          <div className="mt-0.5 shrink-0">
            {EVENT_ICONS[item.event_type] || <MessageSquare className="w-3 h-3 text-gray-500" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-gray-300 break-words">{item.message}</p>
            <div className="flex items-center gap-2 mt-0.5">
              {item.agent && <span className="text-gray-500">{item.agent}</span>}
              <span className="text-gray-600">{formatTime(item.created_at)}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso + 'Z')
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return iso
  }
}
