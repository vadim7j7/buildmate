import { AlertCircle, CheckCircle, Info, MessageSquare, X } from 'lucide-react'
import type { Toast } from '../hooks/useNotifications'

const TOAST_CONFIG = {
  info: {
    icon: <Info className="w-5 h-5 text-accent-400 shrink-0" />,
    borderColor: 'border-accent-500/30',
    bgColor: 'bg-accent-500/5',
    iconBg: 'bg-accent-500/15',
  },
  success: {
    icon: <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />,
    borderColor: 'border-emerald-500/30',
    bgColor: 'bg-emerald-500/5',
    iconBg: 'bg-emerald-500/15',
  },
  warning: {
    icon: <MessageSquare className="w-5 h-5 text-amber-400 shrink-0" />,
    borderColor: 'border-amber-500/30',
    bgColor: 'bg-amber-500/5',
    iconBg: 'bg-amber-500/15',
  },
  error: {
    icon: <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />,
    borderColor: 'border-red-500/30',
    bgColor: 'bg-red-500/5',
    iconBg: 'bg-red-500/15',
  },
}

type ToastContainerProps = {
  toasts: Toast[]
  onDismiss: (id: number) => void
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed top-5 right-5 z-[100] flex flex-col gap-3 max-w-sm">
      {toasts.map(toast => {
        const config = TOAST_CONFIG[toast.type]
        return (
          <div
            key={toast.id}
            className={`
              flex items-start gap-3 p-4 rounded-xl
              bg-surface-900/95 backdrop-blur-md
              border ${config.borderColor}
              shadow-elevated animate-slide-in
              ${toast.onClick ? 'cursor-pointer hover:bg-surface-850' : ''}
              transition-all duration-200
            `}
            onClick={() => {
              toast.onClick?.()
              onDismiss(toast.id)
            }}
          >
            <div className={`p-2 rounded-lg ${config.iconBg}`}>
              {config.icon}
            </div>
            <div className="flex-1 min-w-0 pt-0.5">
              <p className="text-sm font-medium text-gray-100">{toast.title}</p>
              {toast.body && (
                <p className="text-xs text-gray-400 mt-1 line-clamp-2 leading-relaxed">
                  {toast.body}
                </p>
              )}
            </div>
            <button
              onClick={e => { e.stopPropagation(); onDismiss(toast.id) }}
              className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-surface-800 shrink-0 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
