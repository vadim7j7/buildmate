export type AgentColorConfig = {
  bg: string
  text: string
  border: string
}

export const AGENT_COLORS: Record<string, AgentColorConfig> = {
  orchestrator: {
    bg: 'bg-purple-500/15',
    text: 'text-purple-300',
    border: 'border-purple-500/25',
  },
  'frontend-developer': {
    bg: 'bg-accent-500/15',
    text: 'text-accent-300',
    border: 'border-accent-500/25',
  },
  'frontend-tester': {
    bg: 'bg-cyan-500/15',
    text: 'text-cyan-300',
    border: 'border-cyan-500/25',
  },
  'frontend-reviewer': {
    bg: 'bg-indigo-500/15',
    text: 'text-indigo-300',
    border: 'border-indigo-500/25',
  },
  'backend-developer': {
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-300',
    border: 'border-emerald-500/25',
  },
  'backend-tester': {
    bg: 'bg-teal-500/15',
    text: 'text-teal-300',
    border: 'border-teal-500/25',
  },
  'backend-reviewer': {
    bg: 'bg-green-500/15',
    text: 'text-green-300',
    border: 'border-green-500/25',
  },
  'mobile-developer': {
    bg: 'bg-orange-500/15',
    text: 'text-orange-300',
    border: 'border-orange-500/25',
  },
  'mobile-tester': {
    bg: 'bg-amber-500/15',
    text: 'text-amber-300',
    border: 'border-amber-500/25',
  },
  grind: {
    bg: 'bg-red-500/15',
    text: 'text-red-300',
    border: 'border-red-500/25',
  },
  'eval-agent': {
    bg: 'bg-yellow-500/15',
    text: 'text-yellow-300',
    border: 'border-yellow-500/25',
  },
  'security-auditor': {
    bg: 'bg-rose-500/15',
    text: 'text-rose-300',
    border: 'border-rose-500/25',
  },
}

export const DEFAULT_COLOR: AgentColorConfig = {
  bg: 'bg-surface-700/50',
  text: 'text-gray-300',
  border: 'border-surface-600/50',
}

type AgentBadgeProps = {
  agent: string | null
}

export function AgentBadge({ agent }: AgentBadgeProps) {
  if (!agent) return null

  const config = AGENT_COLORS[agent] || DEFAULT_COLOR

  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-1 rounded-lg
        text-[11px] font-medium tracking-wide
        border backdrop-blur-sm transition-colors duration-200
        ${config.bg} ${config.text} ${config.border}
      `}
    >
      {agent}
    </span>
  )
}
