import { createContext, useCallback, useContext, useEffect, useReducer, useRef } from 'react'
import type { ReactNode } from 'react'
import { api, createWebSocket } from '../api/client'
import type { Activity, ProcessStatus, Question, Stats, Task } from '../types'

interface State {
  tasks: Task[]
  stats: Stats
  selectedTaskId: string | null
  selectedActivity: Activity[]
  selectedQuestions: Question[]
  connected: boolean
  processes: Record<string, ProcessStatus>
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
  | { type: 'SET_CONNECTED'; connected: boolean }
  | { type: 'SET_PROCESSES'; processes: Record<string, ProcessStatus> }

const initialState: State = {
  tasks: [],
  stats: { total: 0, pending: 0, in_progress: 0, completed: 0, failed: 0, blocked: 0, pending_questions: 0 },
  selectedTaskId: null,
  selectedActivity: [],
  selectedQuestions: [],
  connected: false,
  processes: {},
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
      return { ...state, selectedTaskId: action.taskId, selectedActivity: [], selectedQuestions: [] }

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

    case 'SET_CONNECTED':
      return { ...state, connected: action.connected }

    case 'SET_PROCESSES':
      return { ...state, processes: action.processes }

    default:
      return state
  }
}

interface DashboardContextValue {
  state: State
  selectTask: (taskId: string | null) => void
  refreshTasks: () => Promise<void>
  refreshStats: () => Promise<void>
}

const DashboardContext = createContext<DashboardContextValue | null>(null)

/** Get the set of task IDs relevant to a selected root task (itself + children). */
function getRelevantTaskIds(tasks: Task[], selectedTaskId: string): Set<string> {
  const task = tasks.find(t => t.id === selectedTaskId)
  const childIds = task?.children?.map(c => c.id) ?? []
  return new Set([selectedTaskId, ...childIds])
}

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
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

  const selectTask = useCallback(async (taskId: string | null) => {
    dispatch({ type: 'SELECT_TASK', taskId })
    if (taskId) {
      try {
        const [activity, questions, task] = await Promise.all([
          api.getActivity(taskId),
          api.getQuestions(taskId),
          api.getTask(taskId),
        ])
        dispatch({ type: 'SET_ACTIVITY', activity })
        dispatch({ type: 'SET_QUESTIONS', questions })
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
            const data = msg.data as { tasks: Task[]; stats: Stats }
            dispatch({ type: 'SET_TASKS', tasks: data.tasks })
            dispatch({ type: 'SET_STATS', stats: data.stats })
            break
          }
          case 'tasks_updated': {
            const tasks = msg.data as Task[]
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
  }, [refreshTasks, refreshStats])

  // Periodic re-fetch of selected task details (activity, questions, children)
  // Acts as a safety net for subtask data that WebSocket filtering may miss
  // when new children are created after the task was selected.
  useEffect(() => {
    const taskId = state.selectedTaskId
    if (!taskId) return

    const interval = setInterval(async () => {
      try {
        const [activity, questions, task] = await Promise.all([
          api.getActivity(taskId),
          api.getQuestions(taskId),
          api.getTask(taskId),
        ])
        dispatch({ type: 'SET_ACTIVITY', activity })
        dispatch({ type: 'SET_QUESTIONS', questions })
        dispatch({ type: 'UPDATE_TASKS', tasks: [task] })
      } catch {
        // ignore
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [state.selectedTaskId])

  return (
    <DashboardContext.Provider value={{ state, selectTask, refreshTasks, refreshStats }}>
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const ctx = useContext(DashboardContext)
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider')
  return ctx
}
