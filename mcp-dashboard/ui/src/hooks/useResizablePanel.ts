import { useCallback, useRef, useSyncExternalStore } from 'react'

const MIN_WIDTH = 320
const MAX_WIDTH = 800
const DEFAULT_WIDTH = 420

/**
 * Module-level store for the shared panel width used by the stacked sidebar
 * (Chat, Team, Services). All three share a single width so the container
 * never has a gap. TaskDetailPanel uses its own independent width.
 */
let stackWidth = DEFAULT_WIDTH
let taskWidth = DEFAULT_WIDTH
const listeners = new Set<() => void>()

function notify() {
  listeners.forEach(fn => fn())
}

function subscribe(cb: () => void) {
  listeners.add(cb)
  return () => { listeners.delete(cb) }
}

/** Read the current width for the stacked sidebar container. */
export function useStackPanelWidth() {
  return useSyncExternalStore(subscribe, () => stackWidth)
}

/**
 * Hook for resizable right-side panels.
 *
 * - `scope="stack"` — shared by Chat, Team, Services (resizing any one resizes all)
 * - `scope="task"` — independent, used only by TaskDetailPanel
 */
export function useResizablePanel(scope: 'stack' | 'task') {
  const getWidth = useCallback(() => scope === 'stack' ? stackWidth : taskWidth, [scope])

  const panelWidth = useSyncExternalStore(subscribe, getWidth)

  const scopeRef = useRef(scope)
  scopeRef.current = scope

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    // Snapshot current width directly from module-level variable at drag start
    const currentWidth = scopeRef.current === 'stack' ? stackWidth : taskWidth
    const originX = e.clientX

    const onMouseMove = (ev: MouseEvent) => {
      const delta = originX - ev.clientX
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, currentWidth + delta))
      if (scopeRef.current === 'stack') {
        stackWidth = newWidth
      } else {
        taskWidth = newWidth
      }
      notify()
    }

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  }, [])

  return { panelWidth, handleResizeStart, MIN_WIDTH, MAX_WIDTH }
}
