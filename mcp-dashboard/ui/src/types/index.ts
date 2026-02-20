export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'blocked'

export type Phase = 'planning' | 'implementation' | 'testing' | 'review' | 'evaluation' | 'completion'

export type QuestionType = 'text' | 'single' | 'multiple' | 'confirm' | 'plan_review'

export interface Task {
  id: string
  parent_id: string | null
  title: string
  description: string
  status: TaskStatus
  assigned_agent: string | null
  phase: string | null
  result: string | null
  auto_accept: boolean
  source: 'cli' | 'dashboard'
  created_at: string
  updated_at: string
  children: Task[]
  pending_questions: number
}

export interface Activity {
  id: number
  task_id: string
  event_type: string
  agent: string | null
  message: string
  metadata: string
  created_at: string
}

export interface Question {
  id: string
  task_id: string
  agent: string | null
  question: string
  question_type: QuestionType
  options: string[] | null
  context: string | null
  answer: string | null
  answered_at: string | null
  auto_accepted: boolean
  created_at: string
}

export interface Stats {
  total: number
  pending: number
  in_progress: number
  completed: number
  failed: number
  blocked: number
  pending_questions: number
}

export interface AgentInfo {
  name: string
  filename: string
  description: string
}

export interface ProcessStatus {
  status: 'running' | 'completed' | 'failed' | 'not_found'
  pid?: number
  exit_code?: number
}

export interface WSMessage {
  type: 'init' | 'tasks_updated' | 'stats' | 'activity' | 'questions' | 'processes' | 'pong'
  data: unknown
}
