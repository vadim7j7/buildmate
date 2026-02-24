import { Award, File, FileText, Image, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'
import type { Artifact } from '../types'

const TYPE_ICON: Record<string, React.ReactNode> = {
  screenshot: <Image className="w-5 h-5 text-accent-400" />,
  markdown_report: <FileText className="w-5 h-5 text-emerald-400" />,
  eval_report: <Award className="w-5 h-5 text-amber-400" />,
  file: <File className="w-5 h-5 text-gray-400" />,
}

type ArtifactModalProps = {
  artifact: Artifact
  onClose: () => void
}

function parseMetadata(artifact: Artifact): Record<string, unknown> {
  try {
    return JSON.parse(artifact.metadata)
  } catch {
    return {}
  }
}

function EvalScoreBars({ metadata }: { metadata: Record<string, unknown> }) {
  const scores = metadata.scores as Record<string, number> | undefined
  if (!scores) return null

  return (
    <div className="space-y-3 mb-5">
      {Object.entries(scores).map(([key, value]) => {
        const pct = typeof value === 'number' ? Math.round(value * 100) : 0
        const colorClass = pct >= 90 ? 'from-emerald-500 to-emerald-400' : pct >= 70 ? 'from-amber-500 to-amber-400' : 'from-red-500 to-red-400'
        const textColor = pct >= 90 ? 'text-emerald-400' : pct >= 70 ? 'text-amber-400' : 'text-red-400'
        return (
          <div key={key}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-gray-400 capitalize font-medium">{key.replace(/_/g, ' ')}</span>
              <span className={`text-xs font-semibold ${textColor}`}>{pct}%</span>
            </div>
            <div className="h-2 rounded-full bg-surface-800 overflow-hidden">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${colorClass} transition-all duration-500`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function ArtifactModal({ artifact, onClose }: ArtifactModalProps) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const metadata = parseMetadata(artifact)
  const icon = TYPE_ICON[artifact.artifact_type] || TYPE_ICON.file
  const evalScore = metadata.final_score as number | undefined
  const evalGrade = metadata.grade as string | undefined

  useEffect(() => {
    if (artifact.artifact_type === 'screenshot') return

    let cancelled = false
    setLoading(true)
    setContent(null)
    api.getArtifactContent(artifact.id)
      .then(text => { if (!cancelled) setContent(text) })
      .catch(() => { if (!cancelled) setContent('[Failed to load content]') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [artifact.id, artifact.artifact_type])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="modal-backdrop animate-fade-in p-8"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="artifact-modal-title"
    >
      <div
        className="modal-content w-full max-w-3xl flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-surface-800/50 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-xl bg-surface-800">
              {icon}
            </div>
            <h2 id="artifact-modal-title" className="text-base font-semibold text-white truncate">
              {artifact.label}
            </h2>
            {evalGrade && (
              <span className={`
                text-xs px-2.5 py-1 rounded-lg font-medium border
                ${(evalScore ?? 0) >= 0.9
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/20'
                  : (evalScore ?? 0) >= 0.7
                    ? 'bg-amber-500/15 text-amber-300 border-amber-500/20'
                    : 'bg-red-500/15 text-red-300 border-red-500/20'
                }
              `}>
                {evalGrade} - {Math.round((evalScore ?? 0) * 100)}%
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors shrink-0 ml-4"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {loading && (
            <div className="flex items-center justify-center py-16">
              <div className="flex items-center gap-3 text-gray-500">
                <div className="w-5 h-5 border-2 border-accent-500/30 border-t-accent-500 rounded-full animate-spin" />
                <span className="text-sm">Loading...</span>
              </div>
            </div>
          )}

          {/* Screenshot */}
          {artifact.artifact_type === 'screenshot' && (
            <img
              src={api.getArtifactContentUrl(artifact.id)}
              alt={artifact.label}
              className="rounded-xl border border-surface-700 max-w-full mx-auto shadow-elevated"
              loading="lazy"
            />
          )}

          {/* Eval report */}
          {artifact.artifact_type === 'eval_report' && (
            <>
              {evalScore != null && (
                <div className="flex items-center gap-4 mb-5 p-4 rounded-xl bg-surface-850 border border-surface-700/50">
                  <span className="text-sm text-gray-400">Overall Score:</span>
                  <span className="text-2xl font-bold text-white">
                    {Math.round(evalScore * 100)}%
                  </span>
                </div>
              )}
              <EvalScoreBars metadata={metadata} />
              {content && (
                <div className="artifact-markdown">
                  <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
                </div>
              )}
            </>
          )}

          {/* Markdown report */}
          {artifact.artifact_type === 'markdown_report' && content && (
            <div className="artifact-markdown">
              <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
            </div>
          )}

          {/* Generic file */}
          {artifact.artifact_type === 'file' && (
            <>
              <p className="text-xs text-gray-500 mb-4 font-mono">{artifact.file_path}</p>
              {content && (
                <div className="artifact-markdown">
                  <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-surface-800/50 flex items-center justify-between shrink-0">
          <span className="text-[11px] text-gray-600 truncate font-mono">{artifact.file_path}</span>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white border border-surface-700 rounded-xl hover:bg-surface-800 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
