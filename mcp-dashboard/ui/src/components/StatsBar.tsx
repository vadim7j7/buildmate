import { AlertCircle, CheckCircle, Circle, Loader, MessageSquare, Wifi, WifiOff, XCircle } from 'lucide-react'
import { useDashboard } from '../context/DashboardContext'

export function StatsBar() {
  const { state } = useDashboard()
  const { stats, connected } = state

  return (
    <div className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-1">
        <h1 className="text-lg font-semibold text-white mr-6">MCP Dashboard</h1>
        <StatPill icon={<Circle className="w-3 h-3" />} label="Pending" count={stats.pending} color="text-gray-400" />
        <StatPill icon={<Loader className="w-3 h-3 animate-spin" />} label="Active" count={stats.in_progress} color="text-yellow-400" />
        <StatPill icon={<CheckCircle className="w-3 h-3" />} label="Done" count={stats.completed} color="text-green-400" />
        <StatPill icon={<XCircle className="w-3 h-3" />} label="Failed" count={stats.failed} color="text-red-400" />
        <StatPill icon={<AlertCircle className="w-3 h-3" />} label="Blocked" count={stats.blocked} color="text-orange-400" />
      </div>

      <div className="flex items-center gap-4">
        {stats.pending_questions > 0 && (
          <div className="flex items-center gap-1.5 text-amber-400 animate-pulse">
            <MessageSquare className="w-4 h-4" />
            <span className="text-sm font-medium">{stats.pending_questions} pending</span>
          </div>
        )}
        <div className={`flex items-center gap-1.5 ${connected ? 'text-green-400' : 'text-red-400'}`}>
          {connected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
          <span className="text-xs">{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>
    </div>
  )
}

function StatPill({ icon, label, count, color }: { icon: React.ReactNode; label: string; count: number; color: string }) {
  return (
    <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-800/50 ${color}`}>
      {icon}
      <span className="text-xs font-medium">{count}</span>
      <span className="text-xs opacity-70">{label}</span>
    </div>
  )
}
