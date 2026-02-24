export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'blocked'

export type Phase = 'planning' | 'implementation' | 'testing' | 'review' | 'evaluation' | 'completion'

export type QuestionType = 'text' | 'single' | 'multiple' | 'confirm' | 'plan_review'

export type ArtifactType = 'screenshot' | 'markdown_report' | 'eval_report' | 'file'

export interface Artifact {
  id: string
  task_id: string
  artifact_type: ArtifactType
  label: string
  file_path: string
  mime_type: string | null
  metadata: string // JSON string
  created_at: string
}

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
  eval_score?: number | null
  eval_grade?: string | null
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
  tools: string[]
  model: string
  skills: string[]
  memory: string | null
}

export interface ProcessStatus {
  status: 'running' | 'completed' | 'failed' | 'not_found'
  pid?: number
  exit_code?: number
}

export interface Service {
  id: string
  name: string
  command: string
  cwd: string
  port: number | null
  status: 'stopped' | 'starting' | 'running' | 'failed'
  pid: number | null
  uptime: number | null
}

export interface ChatSession {
  id: string
  title: string
  claude_session_id: string | null
  model: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: number
  session_id: string
  role: 'user' | 'assistant'
  content: string
  cost_usd: number | null
  duration_ms: number | null
  created_at: string
}

export interface WSMessage {
  type: 'init' | 'tasks_updated' | 'stats' | 'activity' | 'questions' | 'processes' | 'services' | 'pong'
    | 'chat_delta' | 'chat_complete' | 'chat_error' | 'chat_cancelled'
    | 'chat_task_created' | 'chat_task_list' | 'chat_task_info'
    | 'chat_task_cancelled' | 'chat_task_deleted'
  data: unknown
}
