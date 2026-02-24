import { useState } from 'react'
import { ChevronDown, ChevronRight, Brain, Wrench, Zap, Users } from 'lucide-react'
import { useDashboard } from '../context/DashboardContext'
import { AGENT_COLORS, DEFAULT_COLOR } from './AgentBadge'
import type { AgentInfo } from '../types'

function AgentCard({ agent }: { agent: AgentInfo }) {
  const [expanded, setExpanded] = useState(false)
  const colors = AGENT_COLORS[agent.name] || DEFAULT_COLOR

  return (
    <div
      className={`
        bg-surface-900/60 border rounded-xl overflow-hidden
        transition-all duration-200 hover:border-surface-700/50 cursor-pointer
        ${colors.border}
      `}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Collapsed summary */}
      <div className="flex items-center gap-2.5 px-3.5 py-2.5">
        <button className="p-0.5 text-gray-500">
          {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        </button>

        {/* Color dot */}
        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${colors.bg} ring-2 ${colors.border}`} />

        {/* Name */}
        <span className={`text-sm font-medium flex-1 min-w-0 truncate ${colors.text}`}>
          {agent.name}
        </span>

        {/* Model badge */}
        {agent.model && (
          <span className="px-1.5 py-0.5 rounded-md bg-surface-800/80 text-[10px] font-medium text-gray-400 uppercase tracking-wider flex-shrink-0">
            {agent.model}
          </span>
        )}

        {/* Tool count */}
        {agent.tools.length > 0 && (
          <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-surface-800/60 text-[10px] text-gray-500 flex-shrink-0">
            <Wrench className="w-3 h-3" />
            {agent.tools.length}
          </span>
        )}

        {/* Skill count */}
        {agent.skills.length > 0 && (
          <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-surface-800/60 text-[10px] text-gray-500 flex-shrink-0">
            <Zap className="w-3 h-3" />
            {agent.skills.length}
          </span>
        )}
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-surface-800/50 px-3.5 py-3 space-y-3 animate-fade-in-down">
          {/* Description */}
          {agent.description && (
            <p className="text-xs text-gray-400 leading-relaxed">{agent.description}</p>
          )}

          {/* Tools */}
          {agent.tools.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Wrench className="w-3 h-3 text-gray-600" />
                <span className="text-[10px] font-medium text-gray-600 uppercase tracking-wider">Tools</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {agent.tools.map(tool => (
                  <span
                    key={tool}
                    className="px-2 py-0.5 rounded-md bg-surface-800/80 text-[11px] text-gray-300 font-mono"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Skills */}
          {agent.skills.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Zap className="w-3 h-3 text-gray-600" />
                <span className="text-[10px] font-medium text-gray-600 uppercase tracking-wider">Skills</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {agent.skills.map(skill => (
                  <span
                    key={skill}
                    className="px-2 py-0.5 rounded-md bg-accent-500/10 text-[11px] text-accent-400"
                  >
                    /{skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Memory */}
          {agent.memory && (
            <div className="flex items-center gap-1.5">
              <Brain className="w-3 h-3 text-gray-600" />
              <span className="text-[10px] text-gray-500">Memory enabled</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function TeamPanel() {
  const { state } = useDashboard()
  const { agents } = state

  return (
    <div className="w-[420px] border-l border-surface-800/50 bg-surface-900/95 backdrop-blur-md flex flex-col h-full animate-slide-in-right">
      {/* Header */}
      <div className="px-5 py-4 border-b border-surface-800/50">
        <div className="flex items-center gap-2.5">
          <Users className="w-4.5 h-4.5 text-teal-400" />
          <h2 className="text-sm font-semibold text-gray-100">Team</h2>
          <span className="ml-auto px-2 py-0.5 rounded-md bg-surface-800/80 text-xs text-gray-400">
            {agents.length} agents
          </span>
        </div>
      </div>

      {/* Agent list */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {agents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Users className="w-8 h-8 mb-3 opacity-40" />
            <p className="text-sm">No agents found</p>
            <p className="text-xs mt-1 text-gray-600">
              Add files to <code className="text-accent-400 bg-surface-800 px-1 py-0.5 rounded text-[10px]">.claude/agents/</code>
            </p>
          </div>
        ) : (
          agents.map(agent => (
            <AgentCard key={agent.name} agent={agent} />
          ))
        )}
      </div>
    </div>
  )
}
