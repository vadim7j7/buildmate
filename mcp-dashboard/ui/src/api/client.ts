import type { Activity, AgentInfo, Artifact, ChatMessage, ChatSession, ProcessStatus, Question, Service, Stats, Task } from '../types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status}: ${body}`)
  }
  return res.json()
}

export const api = {
  // Tasks
  listTasks: () => request<Task[]>('/tasks'),
  getTask: (id: string) => request<Task>(`/tasks/${id}`),
  createTask: (title: string, description: string, autoAccept: boolean) =>
    request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify({ title, description, auto_accept: autoAccept }),
    }),
  updateTask: (id: string, data: Partial<{ status: string; phase: string; result: string }>) =>
    request<Task>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteTask: (id: string) => request<{ deleted: boolean }>(`/tasks/${id}`, { method: 'DELETE' }),

  // Activity
  getActivity: (taskId: string) => request<Activity[]>(`/tasks/${taskId}/activity`),

  // Questions
  getQuestions: (taskId: string) => request<Question[]>(`/tasks/${taskId}/questions`),
  answerQuestion: (taskId: string, questionId: string, answer: string) =>
    request<Question>(`/tasks/${taskId}/questions/${questionId}/answer`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    }),

  // Process
  runTask: (taskId: string, prompt?: string) =>
    request<{ status: string; task_id: string }>(`/tasks/${taskId}/run`, {
      method: 'POST',
      body: JSON.stringify(prompt ? { prompt } : {}),
    }),
  cancelTask: (taskId: string) =>
    request<{ status: string }>(`/tasks/${taskId}/cancel`, { method: 'POST' }),
  requestChanges: (taskId: string, feedback: string) =>
    request<{ status: string; task_id: string; revision_count: number }>(
      `/tasks/${taskId}/request-changes`,
      { method: 'POST', body: JSON.stringify({ feedback }) },
    ),
  getProcessStatus: (taskId: string) =>
    request<ProcessStatus>(`/tasks/${taskId}/process`),

  // Artifacts
  getArtifacts: (taskId: string) => request<Artifact[]>(`/tasks/${taskId}/artifacts`),
  getArtifactContentUrl: (artifactId: string) => `${BASE}/artifacts/${artifactId}/content`,
  getArtifactContent: async (artifactId: string): Promise<string> => {
    const res = await fetch(`${BASE}/artifacts/${artifactId}/content`)
    if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
    return res.text()
  },

  // Stats & Agents
  getStats: () => request<Stats>('/stats'),
  getAgents: () => request<AgentInfo[]>('/agents'),

  // Services
  listServices: () => request<Service[]>('/services'),
  startService: (id: string) => request<Service>(`/services/${id}/start`, { method: 'POST' }),
  stopService: (id: string) => request<Service>(`/services/${id}/stop`, { method: 'POST' }),
  restartService: (id: string) => request<Service>(`/services/${id}/restart`, { method: 'POST' }),
  getServiceLogs: (id: string, limit = 200) => request<{ logs: string[] }>(`/services/${id}/logs?limit=${limit}`),

  // Chat
  listChatSessions: () => request<ChatSession[]>('/chat/sessions'),
  createChatSession: () => request<ChatSession>('/chat/sessions', { method: 'POST' }),
  getChatSession: (id: string) => request<ChatSession>(`/chat/sessions/${id}`),
  updateChatSession: (id: string, title: string) =>
    request<ChatSession>(`/chat/sessions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),
  deleteChatSession: (id: string) =>
    request<{ deleted: boolean }>(`/chat/sessions/${id}`, { method: 'DELETE' }),
  getChatMessages: (id: string) => request<ChatMessage[]>(`/chat/sessions/${id}/messages`),
  chatSend: (message: string, sessionId?: string, model?: string) =>
    request<{ session_id: string; status: string }>('/chat/send', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId, model }),
    }),
  cancelChat: (sessionId: string) =>
    request<{ status: string }>(`/chat/sessions/${sessionId}/cancel`, { method: 'POST' }),
}

// --- WebSocket hook ---

export function createWebSocket(
  onMessage: (msg: { type: string; data: unknown }) => void,
  onStatusChange: (connected: boolean) => void,
): { close: () => void } {
  let ws: WebSocket | null = null
  let reconnectDelay = 1000
  let closed = false
  let pingInterval: ReturnType<typeof setInterval> | null = null

  function connect() {
    if (closed) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws`
    ws = new WebSocket(url)

    ws.onopen = () => {
      reconnectDelay = 1000
      onStatusChange(true)
      // Start ping interval
      pingInterval = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type !== 'pong') {
          onMessage(msg)
        }
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      onStatusChange(false)
      if (pingInterval) clearInterval(pingInterval)
      if (!closed) {
        setTimeout(connect, reconnectDelay)
        reconnectDelay = Math.min(reconnectDelay * 2, 30000)
      }
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  connect()

  return {
    close: () => {
      closed = true
      if (pingInterval) clearInterval(pingInterval)
      ws?.close()
    },
  }
}
