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
  claude_session_id: string | null
  revision_count: number
  auto_accept: boolean
  source: 'cli' | 'dashboard'
  input_tokens: number
  output_tokens: number
  cost_usd: number
  duration_ms: number
  num_turns: number
  created_at: string
  updated_at: string
  children: Task[]
  pending_questions: number
  eval_score?: number | null
  eval_grade?: string | null
}

export interface TaskRevision {
  id: number
  task_id: string
  revision_number: number
  input_tokens: number
  output_tokens: number
  cost_usd: number
  duration_ms: number
  num_turns: number
  status: string | null
  result: string | null
  feedback: string | null
  created_at: string
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

export interface Document {
  id: string
  title: string
  content: string
  folder: string
  created_at: string
  updated_at: string
}

export interface TaskDoc {
  id: string
  task_id: string
  label: string
  file_path: string
  artifact_type: string
  mime_type: string | null
  content: string
  task_title: string
  created_at: string
}

export interface TaskImage {
  id: string
  task_id: string
  filename: string
  original_name: string
  mime_type: string
  size_bytes: number
  created_at: string
}

export interface WSMessage {
  type: 'init' | 'tasks_updated' | 'stats' | 'activity' | 'questions' | 'artifacts' | 'processes' | 'services' | 'pong'
    | 'chat_delta' | 'chat_complete' | 'chat_error' | 'chat_cancelled'
    | 'chat_task_created' | 'chat_task_list' | 'chat_task_info'
    | 'chat_task_cancelled' | 'chat_task_deleted'
  data: unknown
}
