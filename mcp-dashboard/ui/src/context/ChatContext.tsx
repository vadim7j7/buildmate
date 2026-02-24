import { createContext, useCallback, useContext, useEffect, useReducer, useRef } from 'react'
import type { ReactNode } from 'react'
import { api } from '../api/client'
import type { ChatMessage, ChatSession, Task } from '../types'
import { dashboardRefreshRef } from './DashboardContext'

interface ChatState {
  sessions: ChatSession[]
  activeSessionId: string | null
  messages: ChatMessage[]
  streamingText: string
  isStreaming: boolean
  chatOpen: boolean
  taskResults: Record<string, { tasks: Task[]; query?: string }>
  createdTaskIds: Record<string, string[]>
}

type ChatAction =
  | { type: 'SET_SESSIONS'; sessions: ChatSession[] }
  | { type: 'SET_ACTIVE_SESSION'; sessionId: string | null }
  | { type: 'SET_MESSAGES'; messages: ChatMessage[] }
  | { type: 'ADD_USER_MESSAGE'; message: ChatMessage }
  | { type: 'APPEND_DELTA'; sessionId: string; delta: string }
  | { type: 'STREAM_COMPLETE'; sessionId: string }
  | { type: 'STREAM_ERROR'; sessionId: string }
  | { type: 'STREAM_CANCELLED'; sessionId: string }
  | { type: 'TOGGLE_CHAT' }
  | { type: 'OPEN_CHAT' }
  | { type: 'CLOSE_CHAT' }
  | { type: 'SET_TASK_RESULTS'; sessionId: string; tasks: Task[]; query?: string }
  | { type: 'ADD_CREATED_TASK_ID'; sessionId: string; taskId: string }

const initialState: ChatState = {
  sessions: [],
  activeSessionId: null,
  messages: [],
  streamingText: '',
  isStreaming: false,
  chatOpen: false,
  taskResults: {},
  createdTaskIds: {},
}

function reducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_SESSIONS':
      return { ...state, sessions: action.sessions }
    case 'SET_ACTIVE_SESSION':
      return { ...state, activeSessionId: action.sessionId, messages: [], streamingText: '', isStreaming: false }
    case 'SET_MESSAGES':
      return { ...state, messages: action.messages }
    case 'ADD_USER_MESSAGE':
      return { ...state, messages: [...state.messages, action.message], isStreaming: true, streamingText: '' }
    case 'APPEND_DELTA':
      if (action.sessionId !== state.activeSessionId) return state
      return { ...state, streamingText: state.streamingText + action.delta }
    case 'STREAM_COMPLETE':
      if (action.sessionId !== state.activeSessionId) return { ...state }
      return { ...state, isStreaming: false, streamingText: '' }
    case 'STREAM_ERROR':
      if (action.sessionId !== state.activeSessionId) return state
      return { ...state, isStreaming: false, streamingText: '' }
    case 'STREAM_CANCELLED':
      if (action.sessionId !== state.activeSessionId) return state
      return { ...state, isStreaming: false, streamingText: '' }
    case 'TOGGLE_CHAT':
      return { ...state, chatOpen: !state.chatOpen }
    case 'OPEN_CHAT':
      return { ...state, chatOpen: true }
    case 'CLOSE_CHAT':
      return { ...state, chatOpen: false }
    case 'SET_TASK_RESULTS':
      return { ...state, taskResults: { ...state.taskResults, [action.sessionId]: { tasks: action.tasks, query: action.query } } }
    case 'ADD_CREATED_TASK_ID': {
      const prev = state.createdTaskIds[action.sessionId] ?? []
      return { ...state, createdTaskIds: { ...state.createdTaskIds, [action.sessionId]: [...prev, action.taskId] } }
    }
    default:
      return state
  }
}

interface ChatContextValue {
  state: ChatState
  toggleChat: () => void
  openChat: () => void
  closeChat: () => void
  loadSessions: () => Promise<void>
  selectSession: (sessionId: string | null) => Promise<void>
  sendMessage: (message: string, model?: string) => Promise<void>
  deleteSession: (sessionId: string) => Promise<void>
  cancelStreaming: () => Promise<void>
}

const ChatContext = createContext<ChatContextValue | null>(null)

// Ref for DashboardContext to forward WS messages into ChatContext
export const chatWsHandlerRef: { current: ((msg: { type: string; data: unknown }) => void) | null } = { current: null }

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const activeSessionIdRef = useRef(state.activeSessionId)
  activeSessionIdRef.current = state.activeSessionId

  const loadSessions = useCallback(async () => {
    try {
      const sessions = await api.listChatSessions()
      dispatch({ type: 'SET_SESSIONS', sessions })
    } catch {
      // ignore
    }
  }, [])

  const selectSession = useCallback(async (sessionId: string | null) => {
    dispatch({ type: 'SET_ACTIVE_SESSION', sessionId })
    if (sessionId) {
      try {
        const messages = await api.getChatMessages(sessionId)
        dispatch({ type: 'SET_MESSAGES', messages })
      } catch {
        // ignore
      }
    }
  }, [])

  const sendMessage = useCallback(async (message: string, model?: string) => {
    const sessionId = activeSessionIdRef.current

    // Optimistic user message
    const tempMsg: ChatMessage = {
      id: Date.now(),
      session_id: sessionId || '',
      role: 'user',
      content: message,
      cost_usd: null,
      duration_ms: null,
      created_at: new Date().toISOString(),
    }

    try {
      const result = await api.chatSend(message, sessionId || undefined, model)

      // If a new session was created, update the active session
      if (!sessionId) {
        dispatch({ type: 'SET_ACTIVE_SESSION', sessionId: result.session_id })
        tempMsg.session_id = result.session_id
      }

      dispatch({ type: 'ADD_USER_MESSAGE', message: tempMsg })

      // Refresh sessions list to pick up the new/updated session
      loadSessions()
    } catch {
      // ignore
    }
  }, [loadSessions])

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await api.deleteChatSession(sessionId)
      if (activeSessionIdRef.current === sessionId) {
        dispatch({ type: 'SET_ACTIVE_SESSION', sessionId: null })
      }
      loadSessions()
    } catch {
      // ignore
    }
  }, [loadSessions])

  const cancelStreaming = useCallback(async () => {
    const sessionId = activeSessionIdRef.current
    if (sessionId) {
      try {
        await api.cancelChat(sessionId)
      } catch {
        // ignore
      }
    }
  }, [])

  const toggleChat = useCallback(() => dispatch({ type: 'TOGGLE_CHAT' }), [])
  const openChat = useCallback(() => dispatch({ type: 'OPEN_CHAT' }), [])
  const closeChat = useCallback(() => dispatch({ type: 'CLOSE_CHAT' }), [])

  // Register WS handler
  useEffect(() => {
    chatWsHandlerRef.current = (msg) => {
      const data = msg.data as Record<string, unknown>
      switch (msg.type) {
        case 'chat_delta':
          dispatch({
            type: 'APPEND_DELTA',
            sessionId: data.session_id as string,
            delta: data.delta as string,
          })
          break
        case 'chat_complete': {
          const sessionId = data.session_id as string
          dispatch({ type: 'STREAM_COMPLETE', sessionId })
          // Re-fetch messages to get the persisted assistant message
          if (activeSessionIdRef.current === sessionId) {
            api.getChatMessages(sessionId).then(messages => {
              dispatch({ type: 'SET_MESSAGES', messages })
            }).catch(() => {})
          }
          loadSessions()
          break
        }
        case 'chat_error':
          dispatch({ type: 'STREAM_ERROR', sessionId: data.session_id as string })
          break
        case 'chat_cancelled':
          dispatch({ type: 'STREAM_CANCELLED', sessionId: data.session_id as string })
          break
        case 'chat_task_created': {
          const taskData = data as { session_id: string; task: { id: string } }
          dispatch({ type: 'ADD_CREATED_TASK_ID', sessionId: taskData.session_id, taskId: taskData.task.id })
          dashboardRefreshRef.current?.()
          break
        }
        case 'chat_task_cancelled':
        case 'chat_task_deleted':
          // Task was mutated from chat — refresh the dashboard
          dashboardRefreshRef.current?.()
          break
        case 'chat_task_list': {
          const listData = data as { session_id: string; tasks: Task[]; query?: string }
          dispatch({ type: 'SET_TASK_RESULTS', sessionId: listData.session_id, tasks: listData.tasks, query: listData.query })
          break
        }
        case 'chat_task_info':
          // Info-only events — data is in the chat message text, no dashboard refresh needed
          break
      }
    }
    return () => {
      chatWsHandlerRef.current = null
    }
  }, [loadSessions])

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  return (
    <ChatContext.Provider value={{
      state,
      toggleChat,
      openChat,
      closeChat,
      loadSessions,
      selectSession,
      sendMessage,
      deleteSession,
      cancelStreaming,
    }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within ChatProvider')
  return ctx
}
