import { useEffect, useRef, useState, useCallback } from 'react'
import { ArrowLeft, MessageCircle, Plus, Send, Square, Trash2 } from 'lucide-react'
import { useChat } from '../context/ChatContext'
import { useDashboard } from '../context/DashboardContext'
import { ChatBubble, StreamingBubble } from './ChatBubble'

export function ChatPanel() {
  const { state, selectSession, sendMessage, deleteSession, cancelStreaming } = useChat()
  const { selectTask } = useDashboard()
  const { sessions, activeSessionId, messages, streamingText, isStreaming, taskResults, createdTaskIds } = state

  const handleViewTask = useCallback((taskId: string) => {
    selectTask(taskId)
  }, [selectTask])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Current session's taskResults and createdTaskIds
  const sessionTaskResults = activeSessionId ? taskResults[activeSessionId] : undefined
  const sessionCreatedTaskIds = activeSessionId ? createdTaskIds[activeSessionId] : undefined

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  useEffect(() => {
    if (activeSessionId !== null || sessions.length === 0) {
      inputRef.current?.focus()
    }
  }, [activeSessionId, sessions.length])

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || isStreaming) return
    setInput('')
    await sendMessage(msg)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr + 'Z')
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  // Session list mode
  if (activeSessionId === null) {
    return (
      <div className="w-[420px] border-l border-surface-800/50 bg-surface-900/95 backdrop-blur-md flex flex-col h-full animate-slide-in-right">
        {/* Header */}
        <div className="px-5 py-4 border-b border-surface-800/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent-500/15">
              <MessageCircle className="w-4 h-4 text-accent-400" />
            </div>
            <h2 className="text-base font-semibold text-gray-100">Chat</h2>
          </div>
          <button
            onClick={() => selectSession(null)}
            className="
              flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
              bg-gradient-to-r from-accent-600 to-accent-500 text-white
              shadow-glow-sm hover:from-accent-500 hover:to-accent-400
              transition-all duration-200 active:scale-[0.98]
            "
          >
            <Plus className="w-3.5 h-3.5" />
            New Chat
          </button>
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-y-auto">
          {sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 px-8 text-center">
              <div className="w-16 h-16 rounded-2xl bg-surface-800/50 flex items-center justify-center mb-4">
                <MessageCircle className="w-8 h-8 opacity-30" />
              </div>
              <p className="text-sm font-medium text-gray-400">No conversations yet</p>
              <p className="text-xs mt-2 text-gray-600">Start a chat to ask about your codebase or manage tasks</p>
            </div>
          ) : (
            <div className="py-2">
              {sessions.map(session => (
                <div
                  key={session.id}
                  className="
                    group mx-2 mb-1 px-4 py-3 rounded-xl
                    hover:bg-surface-800/50 cursor-pointer
                    flex items-start gap-3 transition-colors
                  "
                  onClick={() => selectSession(session.id)}
                >
                  <div className="w-8 h-8 rounded-lg bg-surface-800 flex items-center justify-center flex-shrink-0">
                    <MessageCircle className="w-4 h-4 text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-200 font-medium truncate">{session.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[11px] text-gray-500">{formatTime(session.updated_at)}</span>
                      <span className="text-[10px] text-gray-600 bg-surface-800 px-2 py-0.5 rounded-md font-medium">
                        {session.model}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteSession(session.id) }}
                    className="
                      opacity-0 group-hover:opacity-100 p-2 rounded-lg
                      text-gray-500 hover:text-red-400 hover:bg-red-500/10
                      transition-all duration-200
                    "
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-surface-800/50 p-4">
          <div className="flex gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your codebase or manage tasks..."
              rows={1}
              className="
                flex-1 bg-surface-850 border border-surface-700 rounded-xl
                px-4 py-3 text-sm text-gray-100 resize-none
                placeholder-gray-500 transition-all duration-200
                focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
              "
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="
                p-3 rounded-xl bg-gradient-to-r from-accent-600 to-accent-500
                text-white shadow-glow-sm
                hover:from-accent-500 hover:to-accent-400
                disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none
                transition-all duration-200 active:scale-[0.98]
              "
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Active Chat Mode
  return (
    <div className="w-[420px] border-l border-surface-800/50 bg-surface-900/95 backdrop-blur-md flex flex-col h-full animate-slide-in-right">
      {/* Header */}
      <div className="px-5 py-4 border-b border-surface-800/50 flex items-center gap-3">
        <button
          onClick={() => selectSession(null)}
          className="p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-surface-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="text-sm font-semibold text-gray-100 truncate">
            {sessions.find(s => s.id === activeSessionId)?.title || 'Chat'}
          </h2>
        </div>
        <button
          onClick={() => { selectSession(null); sendMessage.length }}
          className="p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-surface-800 transition-colors"
          title="New chat"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-center">
            <div className="w-12 h-12 rounded-xl bg-surface-800/50 flex items-center justify-center mb-3">
              <MessageCircle className="w-6 h-6 opacity-50" />
            </div>
            <p className="text-sm">Send a message to start chatting</p>
          </div>
        )}
        {messages.map(msg => (
          <ChatBubble
            key={msg.id}
            message={msg}
            onViewTask={handleViewTask}
            taskResults={sessionTaskResults}
            createdTaskIds={sessionCreatedTaskIds}
          />
        ))}
        {isStreaming && <StreamingBubble text={streamingText} />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-surface-800/50 p-4">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your codebase or manage tasks..."
            rows={1}
            className="
              flex-1 bg-surface-850 border border-surface-700 rounded-xl
              px-4 py-3 text-sm text-gray-100 resize-none
              placeholder-gray-500 transition-all duration-200
              focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
            "
          />
          {isStreaming ? (
            <button
              onClick={cancelStreaming}
              className="
                p-3 rounded-xl bg-red-600 text-white
                hover:bg-red-500 transition-colors
              "
              title="Stop"
            >
              <Square className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="
                p-3 rounded-xl bg-gradient-to-r from-accent-600 to-accent-500
                text-white shadow-glow-sm
                hover:from-accent-500 hover:to-accent-400
                disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none
                transition-all duration-200 active:scale-[0.98]
              "
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
