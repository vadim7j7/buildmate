import { GripVertical } from 'lucide-react'

export function ResizeHandle({ onMouseDown }: { onMouseDown: (e: React.MouseEvent) => void }) {
  return (
    <div
      onMouseDown={onMouseDown}
      className="absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize z-10 group hover:bg-accent-500/30 transition-colors"
    >
      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-4 h-8 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
        <GripVertical className="w-3 h-3 text-gray-500" />
      </div>
    </div>
  )
}
