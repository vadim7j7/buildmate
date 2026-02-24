import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ListTodo, Play, XCircle, Trash2, Info, ExternalLink, Search } from 'lucide-react'
import type { ChatMessage, Task } from '../types'

const TASK_ACTION_RE = /<task_action>(.*?)<\/task_action>/gs

interface TaskAction {
  action: string
  title?: string
  description?: string
  task_id?: string
  query?: string
}

function parseTaskActions(content: string): { cleanContent: string; actions: TaskAction[] } {
  const actions: TaskAction[] = []
  const cleanContent = content.replace(TASK_ACTION_RE, (_match, json) => {
    try {
      actions.push(JSON.parse(json.trim()))
    } catch {
      // ignore unparseable blocks
    }
    return ''
  }).trim()
  return { cleanContent, actions }
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-400',
  in_progress: 'bg-accent-400',
  completed: 'bg-emerald-400',
  failed: 'bg-red-400',
  blocked: 'bg-amber-400',
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  in_progress: 'Running',
  completed: 'Done',
  failed: 'Failed',
  blocked: 'Blocked',
}

function TaskMiniCard({ task, onViewTask }: { task: Task; onViewTask?: (taskId: string) => void }) {
  return (
    <button
      onClick={() => onViewTask?.(task.id)}
      className="
        w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg
        hover:bg-surface-700/50 transition-colors group text-left
      "
    >
      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${STATUS_COLORS[task.status] ?? 'bg-gray-400'}`} />
      <span className="flex-1 text-sm text-gray-200 truncate">{task.title}</span>
      <span className="text-[10px] text-gray-500 font-medium flex-shrink-0">
        {STATUS_LABELS[task.status] ?? task.status}
      </span>
      <ExternalLink className="w-3 h-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
    </button>
  )
}

function TaskListCard({ tasks, query, onViewTask }: { tasks: Task[]; query?: string; onViewTask?: (taskId: string) => void }) {
  const header = query
    ? `Tasks matching '${query}' (${tasks.length})`
    : `All Tasks (${tasks.length})`

  return (
    <div className="my-2 rounded-xl border border-accent-500/30 bg-accent-500/10 px-3 py-2">
      <div className="flex items-center gap-2 text-xs font-medium text-accent-400 mb-1">
        {query ? <Search className="w-3.5 h-3.5" /> : <ListTodo className="w-3.5 h-3.5" />}
        {header}
      </div>
      {tasks.length > 0 ? (
        <div className="max-h-60 overflow-y-auto -mx-1">
          {tasks.map(task => (
            <TaskMiniCard key={task.id} task={task} onViewTask={onViewTask} />
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-500 py-2 text-center">No tasks found</p>
      )}
    </div>
  )
}

interface TaskActionCardProps {
  action: TaskAction
  onViewTask?: (taskId: string) => void
  createdTaskId?: string
  taskResults?: { tasks: Task[]; query?: string }
}

function TaskActionCard({ action, onViewTask, createdTaskId, taskResults }: TaskActionCardProps) {
  switch (action.action) {
    case 'create_task':
      return (
        <div className="my-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2">
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-400">
            <Play className="w-3.5 h-3.5" />
            Task Created
            {createdTaskId && (
              <button
                onClick={() => onViewTask?.(createdTaskId)}
                className="ml-auto text-[10px] text-accent-400 hover:text-accent-300 flex items-center gap-1"
              >
                View <ExternalLink className="w-2.5 h-2.5" />
              </button>
            )}
          </div>
          <p className="mt-1 text-sm text-gray-200 font-medium">{action.title}</p>
          {action.description && (
            <p className="mt-0.5 text-xs text-gray-400 line-clamp-2">{action.description}</p>
          )}
        </div>
      )
    case 'cancel_task':
      return (
        <div className="my-2 rounded-xl border border-gray-500/30 bg-gray-500/10 px-3 py-2">
          <div className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <XCircle className="w-3.5 h-3.5" />
            Task Cancelled
            {action.task_id && (
              <button
                onClick={() => onViewTask?.(action.task_id!)}
                className="ml-auto text-[10px] text-accent-400 hover:text-accent-300"
              >
                View
              </button>
            )}
          </div>
        </div>
      )
    case 'delete_task':
      return (
        <div className="my-2 rounded-xl border border-gray-500/30 bg-gray-500/10 px-3 py-2">
          <div className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <Trash2 className="w-3.5 h-3.5" />
            Task Deleted
          </div>
        </div>
      )
    case 'list_tasks':
    case 'search_tasks':
      if (taskResults) {
        return <TaskListCard tasks={taskResults.tasks} query={taskResults.query} onViewTask={onViewTask} />
      }
      return (
        <div className="my-2 rounded-xl border border-accent-500/30 bg-accent-500/10 px-3 py-2">
          <div className="flex items-center gap-2 text-xs font-medium text-accent-400">
            {action.action === 'search_tasks' ? <Search className="w-3.5 h-3.5" /> : <ListTodo className="w-3.5 h-3.5" />}
            {action.action === 'search_tasks' ? `Searched: ${action.query ?? ''}` : 'Listed Tasks'}
          </div>
        </div>
      )
    case 'get_task':
      return (
        <div className="my-2 rounded-xl border border-accent-500/30 bg-accent-500/10 px-3 py-2">
          <div className="flex items-center gap-2 text-xs font-medium text-accent-400">
            <Info className="w-3.5 h-3.5" />
            Task Details
            {action.task_id && (
              <button
                onClick={() => onViewTask?.(action.task_id!)}
                className="ml-auto text-[10px] text-accent-400 hover:text-accent-300"
              >
                View
              </button>
            )}
          </div>
        </div>
      )
    default:
      return null
  }
}

type ChatBubbleProps = {
  message: ChatMessage
  onViewTask?: (taskId: string) => void
  taskResults?: { tasks: Task[]; query?: string }
  createdTaskIds?: string[]
}

export function ChatBubble({ message, onViewTask, taskResults, createdTaskIds }: ChatBubbleProps) {
  const isUser = message.role === 'user'
  const { cleanContent, actions } = isUser
    ? { cleanContent: message.content, actions: [] }
    : parseTaskActions(message.content)

  // Track create_task index to map to createdTaskIds
  let createIdx = 0

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}>
      <div
        className={`
          max-w-[85%] rounded-2xl px-4 py-3
          ${isUser
            ? 'bg-gradient-to-r from-accent-600 to-accent-500 text-white shadow-glow-sm'
            : 'bg-surface-800/80 text-gray-100 border border-surface-700/50'
          }
        `}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <>
            {cleanContent && (
              <div className="chat-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {cleanContent}
                </ReactMarkdown>
              </div>
            )}
            {actions.map((action, i) => {
              const isCreate = action.action === 'create_task'
              const cId = isCreate ? createdTaskIds?.[createIdx] : undefined
              if (isCreate) createIdx++
              const isListOrSearch = action.action === 'list_tasks' || action.action === 'search_tasks'
              return (
                <TaskActionCard
                  key={i}
                  action={action}
                  onViewTask={onViewTask}
                  createdTaskId={cId}
                  taskResults={isListOrSearch ? taskResults : undefined}
                />
              )
            })}
          </>
        )}
        {!isUser && (message.cost_usd != null || message.duration_ms != null) && (
          <div className="mt-2 pt-2 border-t border-surface-700/50 flex gap-4 text-[11px] text-gray-500">
            {message.cost_usd != null && (
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/50" />
                ${message.cost_usd.toFixed(4)}
              </span>
            )}
            {message.duration_ms != null && (
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-500/50" />
                {(message.duration_ms / 1000).toFixed(1)}s
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

type StreamingBubbleProps = {
  text: string
}

export function StreamingBubble({ text }: StreamingBubbleProps) {
  // Strip any partial or complete <task_action> blocks from streaming display
  const displayText = text.replace(TASK_ACTION_RE, '').replace(/<task_action>[^<]*$/, '').trim()

  return (
    <div className="flex justify-start mb-4 animate-fade-in">
      <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-surface-800/80 text-gray-100 border border-surface-700/50">
        {displayText ? (
          <div className="chat-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {displayText}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <div className="flex gap-1">
              <span className="w-2 h-2 rounded-full bg-accent-500 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-accent-500 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-accent-500 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span>Thinking...</span>
          </div>
        )}
        {displayText && <span className="streaming-cursor inline-block" />}
      </div>
    </div>
  )
}
