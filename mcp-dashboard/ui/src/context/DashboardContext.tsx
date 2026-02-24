import { createContext, useCallback, useContext, useEffect, useReducer, useRef } from 'react'
import type { ReactNode } from 'react'
import { api, createWebSocket } from '../api/client'
import type { Activity, AgentInfo, Artifact, ProcessStatus, Question, Service, Stats, Task } from '../types'
import { useNotifications } from '../hooks/useNotifications'
import type { Toast } from '../hooks/useNotifications'
import { chatWsHandlerRef } from './ChatContext'

interface State {
  tasks: Task[]
  stats: Stats
  selectedTaskId: string | null
  selectedActivity: Activity[]
  selectedQuestions: Question[]
  selectedArtifacts: Artifact[]
  connected: boolean
  processes: Record<string, ProcessStatus>
  services: Service[]
  showServices: boolean
  agents: AgentInfo[]
  showTeam: boolean
}

type Action =
  | { type: 'SET_TASKS'; tasks: Task[] }
  | { type: 'UPDATE_TASKS'; tasks: Partial<Task>[] }
  | { type: 'SET_STATS'; stats: Stats }
  | { type: 'SELECT_TASK'; taskId: string | null }
  | { type: 'SET_ACTIVITY'; activity: Activity[] }
  | { type: 'ADD_ACTIVITY'; activity: Activity[] }
  | { type: 'SET_QUESTIONS'; questions: Question[] }
  | { type: 'UPDATE_QUESTIONS'; questions: Question[] }
  | { type: 'SET_ARTIFACTS'; artifacts: Artifact[] }
  | { type: 'SET_CONNECTED'; connected: boolean }
  | { type: 'SET_PROCESSES'; processes: Record<string, ProcessStatus> }
  | { type: 'SET_SERVICES'; services: Service[] }
  | { type: 'TOGGLE_SERVICES' }
  | { type: 'SET_AGENTS'; agents: AgentInfo[] }
  | { type: 'TOGGLE_TEAM' }

const initialState: State = {
  tasks: [],
  stats: { total: 0, pending: 0, in_progress: 0, completed: 0, failed: 0, blocked: 0, pending_questions: 0 },
  selectedTaskId: null,
  selectedActivity: [],
  selectedQuestions: [],
  selectedArtifacts: [],
  connected: false,
  processes: {},
  services: [],
  showServices: false,
  agents: [],
  showTeam: false,
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_TASKS':
      return { ...state, tasks: action.tasks }

    case 'UPDATE_TASKS': {
      const updated = new Map(action.tasks.map(t => [t.id, t]))
      const tasks = state.tasks.map(t => {
        const u = updated.get(t.id)
        return u ? { ...t, ...u } : t
      })
      // Add any new root tasks not already in list
      for (const t of action.tasks) {
        if (!t.parent_id && !tasks.find(existing => existing.id === t.id)) {
          tasks.unshift(t as Task)
        }
      }
      return { ...state, tasks }
    }

    case 'SET_STATS':
      return { ...state, stats: action.stats }

    case 'SELECT_TASK':
      return { ...state, selectedTaskId: action.taskId, selectedActivity: [], selectedQuestions: [], selectedArtifacts: [] }

    case 'SET_ACTIVITY':
      return { ...state, selectedActivity: action.activity }

    case 'ADD_ACTIVITY': {
      const existingIds = new Set(state.selectedActivity.map(a => a.id))
      const newItems = action.activity.filter(a => !existingIds.has(a.id))
      return { ...state, selectedActivity: [...newItems, ...state.selectedActivity] }
    }

    case 'SET_QUESTIONS':
      return { ...state, selectedQuestions: action.questions }

    case 'UPDATE_QUESTIONS': {
      const updatedQ = new Map(action.questions.map(q => [q.id, q]))
      const questions = state.selectedQuestions.map(q => {
        const u = updatedQ.get(q.id)
        return u ? { ...q, ...u } : q
      })
      for (const q of action.questions) {
        if (!questions.find(existing => existing.id === q.id)) {
          questions.push(q as Question)
        }
      }
      return { ...state, selectedQuestions: questions }
    }

    case 'SET_ARTIFACTS':
      return { ...state, selectedArtifacts: action.artifacts }

    case 'SET_CONNECTED':
      return { ...state, connected: action.connected }

    case 'SET_PROCESSES':
      return { ...state, processes: action.processes }

    case 'SET_SERVICES':
      return { ...state, services: action.services }

    case 'TOGGLE_SERVICES':
      return { ...state, showServices: !state.showServices }

    case 'SET_AGENTS':
      return { ...state, agents: action.agents }

    case 'TOGGLE_TEAM':
      return { ...state, showTeam: !state.showTeam }

    default:
      return state
  }
}

interface DashboardContextValue {
  state: State
  selectTask: (taskId: string | null) => void
  refreshTasks: () => Promise<void>
  refreshStats: () => Promise<void>
  toggleServices: () => void
  toggleTeam: () => void
  toasts: Toast[]
  dismissToast: (id: number) => void
}

const DashboardContext = createContext<DashboardContextValue | null>(null)

/** Ref that ChatContext can call to trigger task list + stats refresh from chat actions. */
export const dashboardRefreshRef: { current: (() => void) | null } = { current: null }

/** Get the set of task IDs relevant to a selected root task (itself + children). */
function getRelevantTaskIds(tasks: Task[], selectedTaskId: string): Set<string> {
  const task = tasks.find(t => t.id === selectedTaskId)
  const childIds = task?.children?.map(c => c.id) ?? []
  return new Set([selectedTaskId, ...childIds])
}

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const { notify, toasts, dismissToast } = useNotifications()
  const selectedTaskIdRef = useRef(state.selectedTaskId)
  selectedTaskIdRef.current = state.selectedTaskId
  const tasksRef = useRef(state.tasks)
  tasksRef.current = state.tasks

  const refreshTasks = useCallback(async () => {
    try {
      const tasks = await api.listTasks()
      dispatch({ type: 'SET_TASKS', tasks })
    } catch {
      // ignore
    }
  }, [])

  const refreshStats = useCallback(async () => {
    try {
      const stats = await api.getStats()
      dispatch({ type: 'SET_STATS', stats })
    } catch {
      // ignore
    }
  }, [])

  const toggleServices = useCallback(() => {
    dispatch({ type: 'TOGGLE_SERVICES' })
  }, [])

  const toggleTeam = useCallback(() => {
    dispatch({ type: 'TOGGLE_TEAM' })
  }, [])

  // Fetch agents on mount
  useEffect(() => {
    api.getAgents().then(agents => dispatch({ type: 'SET_AGENTS', agents })).catch(() => {})
  }, [])

  // Expose refresh functions via ref so ChatContext can trigger them
  dashboardRefreshRef.current = () => {
    refreshTasks()
    refreshStats()
  }

  const selectTask = useCallback(async (taskId: string | null) => {
    dispatch({ type: 'SELECT_TASK', taskId })
    if (taskId) {
      try {
        const [activity, questions, task, artifacts] = await Promise.all([
          api.getActivity(taskId),
          api.getQuestions(taskId),
          api.getTask(taskId),
          api.getArtifacts(taskId),
        ])
        dispatch({ type: 'SET_ACTIVITY', activity })
        dispatch({ type: 'SET_QUESTIONS', questions })
        dispatch({ type: 'SET_ARTIFACTS', artifacts })
        // Update the task in the list with fresh children
        dispatch({ type: 'UPDATE_TASKS', tasks: [task] })
      } catch {
        // ignore
      }
    }
  }, [])

  // WebSocket connection
  useEffect(() => {
    const ws = createWebSocket(
      (msg) => {
        switch (msg.type) {
          case 'init': {
            const data = msg.data as { tasks: Task[]; stats: Stats; services?: Service[] }
            dispatch({ type: 'SET_TASKS', tasks: data.tasks })
            dispatch({ type: 'SET_STATS', stats: data.stats })
            if (data.services) {
              dispatch({ type: 'SET_SERVICES', services: data.services })
            }
            break
          }
          case 'tasks_updated': {
            const tasks = msg.data as Task[]
            const prevTasks = tasksRef.current
            for (const task of tasks) {
              const prev = prevTasks.find(t => t.id === task.id)
              if (prev && prev.status !== task.status) {
                if (task.status === 'completed') {
                  notify(`Task completed: ${task.title}`, {
                    tag: 'task-' + task.id,
                    type: 'success',
                    onClick: () => dispatch({ type: 'SELECT_TASK', taskId: task.id }),
                  })
                } else if (task.status === 'failed') {
                  notify(`Task failed: ${task.title}`, {
                    tag: 'task-' + task.id,
                    type: 'error',
                    onClick: () => dispatch({ type: 'SELECT_TASK', taskId: task.id }),
                  })
                }
              }
            }
            dispatch({ type: 'SET_TASKS', tasks })
            break
          }
          case 'stats': {
            const stats = msg.data as Stats
            dispatch({ type: 'SET_STATS', stats })
            break
          }
          case 'activity': {
            const activity = msg.data as Activity[]
            // Include activity from the selected task AND its subtasks
            const taskId = selectedTaskIdRef.current
            if (taskId) {
              const relevantIds = getRelevantTaskIds(tasksRef.current, taskId)
              const relevant = activity.filter(a => relevantIds.has(a.task_id))
              if (relevant.length > 0) {
                dispatch({ type: 'ADD_ACTIVITY', activity: relevant })
              }
            }
            break
          }
          case 'questions': {
            const questions = msg.data as Question[]
            // Notify for unanswered questions
            const unanswered = questions.filter(q => !q.answer)
            if (unanswered.length > 0) {
              const q = unanswered[0]
              notify('Question awaiting answer', {
                body: q.question,
                tag: 'question-' + q.id,
                type: 'warning',
                onClick: () => dispatch({ type: 'SELECT_TASK', taskId: q.task_id }),
              })
            }
            // Include questions from the selected task AND its subtasks
            const taskId = selectedTaskIdRef.current
            if (taskId) {
              const relevantIds = getRelevantTaskIds(tasksRef.current, taskId)
              const relevant = questions.filter(q => relevantIds.has(q.task_id))
              if (relevant.length > 0) {
                dispatch({ type: 'UPDATE_QUESTIONS', questions: relevant })
              }
            }
            // Refresh stats to update pending_questions count
            refreshStats()
            // Refresh tasks to update pending_questions on cards
            refreshTasks()
            break
          }
          case 'processes': {
            const processes = msg.data as Record<string, ProcessStatus>
            dispatch({ type: 'SET_PROCESSES', processes })
            break
          }
          case 'services': {
            const svcList = msg.data as Service[]
            dispatch({ type: 'SET_SERVICES', services: svcList })
            break
          }
          case 'chat_delta':
          case 'chat_complete':
          case 'chat_error':
          case 'chat_cancelled':
          case 'chat_task_created':
          case 'chat_task_list':
          case 'chat_task_info':
          case 'chat_task_cancelled':
          case 'chat_task_deleted': {
            chatWsHandlerRef.current?.(msg)
            break
          }
        }
      },
      (connected) => {
        dispatch({ type: 'SET_CONNECTED', connected })
        if (connected) {
          refreshTasks()
          refreshStats()
        }
      },
    )

    return () => ws.close()
  }, [refreshTasks, refreshStats, notify])

  // Periodic re-fetch of selected task details (activity, questions, children)
  // Acts as a safety net for subtask data that WebSocket filtering may miss
  // when new children are created after the task was selected.
  useEffect(() => {
    const taskId = state.selectedTaskId
    if (!taskId) return

    const interval = setInterval(async () => {
      try {
        const [activity, questions, task, artifacts] = await Promise.all([
          api.getActivity(taskId),
          api.getQuestions(taskId),
          api.getTask(taskId),
          api.getArtifacts(taskId),
        ])
        dispatch({ type: 'SET_ACTIVITY', activity })
        dispatch({ type: 'SET_QUESTIONS', questions })
        dispatch({ type: 'SET_ARTIFACTS', artifacts })
        dispatch({ type: 'UPDATE_TASKS', tasks: [task] })
      } catch {
        // ignore
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [state.selectedTaskId])

  return (
    <DashboardContext.Provider value={{ state, selectTask, refreshTasks, refreshStats, toggleServices, toggleTeam, toasts, dismissToast }}>
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const ctx = useContext(DashboardContext)
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider')
  return ctx
}
