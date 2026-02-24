import { useEffect, useMemo, useRef, useState } from 'react'
import { AlertCircle, CheckCircle, Circle, Loader, MessageCircle, MessageSquare, Search, Server, Wifi, WifiOff, X, XCircle } from 'lucide-react'
import { useDashboard } from '../context/DashboardContext'
import { useChat } from '../context/ChatContext'

const SEARCH_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-400',
  in_progress: 'bg-accent-400',
  completed: 'bg-emerald-400',
  failed: 'bg-red-400',
  blocked: 'bg-amber-400',
}

export function StatsBar() {
  const { state, selectTask, toggleServices } = useDashboard()
  const { stats, connected, services, showServices, tasks } = state
  const { state: chatState, toggleChat } = useChat()

  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const searchInputRef = useRef<HTMLInputElement>(null)
  const searchContainerRef = useRef<HTMLDivElement>(null)

  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return []
    const q = searchQuery.toLowerCase()
    return tasks
      .filter(t => t.title.toLowerCase().includes(q) || t.description.toLowerCase().includes(q))
      .slice(0, 8)
  }, [searchQuery, tasks])

  // Focus input when search opens
  useEffect(() => {
    if (searchOpen) searchInputRef.current?.focus()
  }, [searchOpen])

  // Close on click outside
  useEffect(() => {
    if (!searchOpen) return
    const handler = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setSearchOpen(false)
        setSearchQuery('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [searchOpen])

  // Keyboard shortcut: Cmd/Ctrl+K to toggle search
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setSearchOpen(prev => {
          if (prev) setSearchQuery('')
          return !prev
        })
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  const runningCount = services.filter(s => s.status === 'running').length
  const totalCount = services.length

  return (
    <header className="relative">
      {/* Main header content */}
      <div className="bg-surface-900/80 backdrop-blur-md border-b border-surface-800/50 px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left section: Logo and Stats */}
          <div className="flex items-center gap-6">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-500 to-purple-600 flex items-center justify-center shadow-glow-sm">
                <span className="text-white text-sm font-bold">M</span>
              </div>
              <h1 className="text-lg font-semibold text-white tracking-tight">
                MCP Dashboard
              </h1>
            </div>

            {/* Stats Pills */}
            <div className="flex items-center gap-1.5">
              <StatPill
                icon={<Circle className="w-3.5 h-3.5" />}
                label="Pending"
                count={stats.pending}
                colorClass="text-gray-400"
                bgClass="bg-surface-800/60"
              />
              <StatPill
                icon={<Loader className="w-3.5 h-3.5 animate-spin" />}
                label="Active"
                count={stats.in_progress}
                colorClass="text-amber-400"
                bgClass="bg-amber-500/10"
                glowClass={stats.in_progress > 0 ? 'ring-1 ring-amber-500/20' : ''}
              />
              <StatPill
                icon={<CheckCircle className="w-3.5 h-3.5" />}
                label="Done"
                count={stats.completed}
                colorClass="text-emerald-400"
                bgClass="bg-emerald-500/10"
              />
              <StatPill
                icon={<XCircle className="w-3.5 h-3.5" />}
                label="Failed"
                count={stats.failed}
                colorClass="text-red-400"
                bgClass="bg-red-500/10"
              />
              <StatPill
                icon={<AlertCircle className="w-3.5 h-3.5" />}
                label="Blocked"
                count={stats.blocked}
                colorClass="text-orange-400"
                bgClass="bg-orange-500/10"
              />
            </div>
          </div>

          {/* Search */}
          <div ref={searchContainerRef} className="relative">
            {searchOpen ? (
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" />
                <input
                  ref={searchInputRef}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Escape') { setSearchOpen(false); setSearchQuery('') }
                  }}
                  placeholder="Search tasks..."
                  className="
                    w-64 bg-surface-850 border border-surface-700 rounded-xl
                    pl-9 pr-8 py-2 text-sm text-gray-100
                    placeholder-gray-500 transition-all duration-200
                    focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
                  "
                />
                {searchQuery ? (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                ) : (
                  <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-gray-600 font-medium">ESC</kbd>
                )}
                {searchQuery.trim() && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-surface-850 border border-surface-700 rounded-xl overflow-hidden shadow-2xl z-50 max-h-80 overflow-y-auto">
                    {searchResults.length > 0 ? (
                      searchResults.map(task => (
                        <button
                          key={task.id}
                          onClick={() => {
                            selectTask(task.id)
                            setSearchOpen(false)
                            setSearchQuery('')
                          }}
                          className="
                            w-full flex items-center gap-2.5 px-3.5 py-2.5 text-left
                            hover:bg-surface-700/50 transition-colors border-b border-surface-800/30 last:border-0
                          "
                        >
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${SEARCH_STATUS_COLORS[task.status] ?? 'bg-gray-400'}`} />
                          <span className="flex-1 text-sm text-gray-200 truncate">{task.title}</span>
                          <span className="text-[10px] text-gray-500 font-medium flex-shrink-0 capitalize">
                            {task.status.replace('_', ' ')}
                          </span>
                        </button>
                      ))
                    ) : (
                      <p className="text-xs text-gray-500 py-4 text-center">No tasks found</p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setSearchOpen(true)}
                className="
                  flex items-center gap-2 px-4 py-2 rounded-xl text-sm
                  bg-surface-800/60 text-gray-400 hover:text-gray-200 hover:bg-surface-800
                  transition-all duration-200
                "
              >
                <Search className="w-4 h-4" />
                <span>Search</span>
                <kbd className="ml-1 text-[10px] text-gray-600 bg-surface-700/50 px-1.5 py-0.5 rounded-md font-medium">
                  {navigator.platform?.includes('Mac') ? '\u2318' : 'Ctrl'}K
                </kbd>
              </button>
            )}
          </div>

          {/* Right section: Actions and Status */}
          <div className="flex items-center gap-3">
            {/* Chat Toggle */}
            <button
              onClick={toggleChat}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                transition-all duration-200
                ${chatState.chatOpen
                  ? 'bg-accent-500/20 text-accent-300 ring-1 ring-accent-500/30 shadow-glow-sm'
                  : 'bg-surface-800/60 text-gray-400 hover:text-gray-200 hover:bg-surface-800'
                }
              `}
            >
              <MessageCircle className="w-4 h-4" />
              <span>Chat</span>
            </button>

            {/* Services Toggle */}
            {totalCount > 0 && (
              <button
                onClick={toggleServices}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                  transition-all duration-200
                  ${showServices
                    ? 'bg-purple-500/20 text-purple-300 ring-1 ring-purple-500/30'
                    : 'bg-surface-800/60 text-gray-400 hover:text-gray-200 hover:bg-surface-800'
                  }
                `}
              >
                <Server className="w-4 h-4" />
                <span>Services</span>
                <span className="px-1.5 py-0.5 rounded-md bg-surface-700/50 text-xs">
                  {runningCount}/{totalCount}
                </span>
              </button>
            )}

            {/* Pending Questions Alert */}
            {stats.pending_questions > 0 && (
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/15 ring-1 ring-amber-500/30 animate-pulse-subtle">
                <MessageSquare className="w-4 h-4 text-amber-400" />
                <span className="text-sm font-medium text-amber-300">
                  {stats.pending_questions} pending
                </span>
              </div>
            )}

            {/* Connection Status */}
            <div
              className={`
                flex items-center gap-2 px-4 py-2 rounded-xl text-sm
                transition-all duration-300
                ${connected
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : 'bg-red-500/10 text-red-400'
                }
              `}
            >
              {connected ? (
                <>
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
                  </span>
                  <Wifi className="w-4 h-4" />
                  <span className="font-medium">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4" />
                  <span className="font-medium">Disconnected</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Gradient border accent */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent-500/50 to-transparent" />
    </header>
  )
}

type StatPillProps = {
  icon: React.ReactNode
  label: string
  count: number
  colorClass: string
  bgClass: string
  glowClass?: string
}

function StatPill({ icon, label, count, colorClass, bgClass, glowClass = '' }: StatPillProps) {
  return (
    <div
      className={`
        flex items-center gap-2 px-3.5 py-2 rounded-xl
        backdrop-blur-sm transition-all duration-200
        ${bgClass} ${colorClass} ${glowClass}
      `}
    >
      {icon}
      <span className="text-sm font-semibold tabular-nums">{count}</span>
      <span className="text-xs opacity-70">{label}</span>
    </div>
  )
}
