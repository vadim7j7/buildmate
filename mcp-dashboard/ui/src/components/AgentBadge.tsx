const AGENT_COLORS: Record<string, string> = {
  orchestrator: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  'frontend-developer': 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  'frontend-tester': 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  'frontend-reviewer': 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
  'backend-developer': 'bg-green-500/20 text-green-300 border-green-500/30',
  'backend-tester': 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  'backend-reviewer': 'bg-teal-500/20 text-teal-300 border-teal-500/30',
  'mobile-developer': 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  'mobile-tester': 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  grind: 'bg-red-500/20 text-red-300 border-red-500/30',
  'eval-agent': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  'security-auditor': 'bg-rose-500/20 text-rose-300 border-rose-500/30',
}

const DEFAULT_COLOR = 'bg-gray-500/20 text-gray-300 border-gray-500/30'

export function AgentBadge({ agent }: { agent: string | null }) {
  if (!agent) return null
  const color = AGENT_COLORS[agent] || DEFAULT_COLOR
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${color}`}>
      {agent}
    </span>
  )
}
