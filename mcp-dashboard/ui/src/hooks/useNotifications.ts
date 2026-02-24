import { useCallback, useEffect, useRef, useState } from 'react'

export interface Toast {
  id: number
  title: string
  body?: string
  type: 'info' | 'success' | 'warning' | 'error'
  /** If set, clicking the toast calls this */
  onClick?: () => void
}

let nextId = 0

export function useNotifications() {
  const [toasts, setToasts] = useState<Toast[]>([])
  const seenTags = useRef(new Set<string>())

  // Request browser notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      (async () => {
        await Notification.requestPermission();
      })();
    }
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const notify = useCallback((
    title: string,
    options?: NotificationOptions & {
      type?: Toast['type']
      onClick?: () => void
      /** Deduplicate: skip if this tag was already shown */
      tag?: string
    },
  ) => {
    // Deduplicate by tag
    if (options?.tag) {
      if (seenTags.current.has(options.tag)) return
      seenTags.current.add(options.tag)
    }

    // In-app toast (always works)
    const id = ++nextId
    const toast: Toast = {
      id,
      title,
      body: options?.body,
      type: options?.type ?? 'info',
      onClick: options?.onClick,
    }
    setToasts(prev => [...prev, toast])

    // Auto-dismiss after 6 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 6000)

    // Browser notification (bonus, when tab is hidden)
    if (
      document.visibilityState !== 'visible' &&
      'Notification' in window &&
      Notification.permission === 'granted'
    ) {
      const n = new Notification(title, { icon: '/favicon.ico', ...options })
      n.onclick = () => { window.focus(); n.close() }
    }
  }, [])

  /** Clear a dedup tag so the same notification can fire again */
  const clearTag = useCallback((tag: string) => {
    seenTags.current.delete(tag)
  }, [])

  return { notify, toasts, dismissToast, clearTag }
}
