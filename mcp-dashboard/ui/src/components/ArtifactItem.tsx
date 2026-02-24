import { Award, File, FileText, Image } from 'lucide-react'
import type { Artifact } from '../types'

const TYPE_ICON: Record<string, React.ReactNode> = {
  screenshot: <Image className="w-3.5 h-3.5 text-blue-400" />,
  markdown_report: <FileText className="w-3.5 h-3.5 text-green-400" />,
  eval_report: <Award className="w-3.5 h-3.5 text-amber-400" />,
  file: <File className="w-3.5 h-3.5 text-gray-400" />,
}

interface Props {
  artifact: Artifact
  onClick: () => void
}

function parseMetadata(artifact: Artifact): Record<string, unknown> {
  try {
    return JSON.parse(artifact.metadata)
  } catch {
    return {}
  }
}

export function ArtifactItem({ artifact, onClick }: Props) {
  const metadata = parseMetadata(artifact)
  const icon = TYPE_ICON[artifact.artifact_type] || TYPE_ICON.file
  const evalGrade = metadata.grade as string | undefined
  const evalScore = metadata.final_score as number | undefined

  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-700/50 hover:bg-gray-800/50 transition-colors text-left"
    >
      {icon}
      <span className="text-xs text-gray-200 flex-1 truncate">{artifact.label}</span>
      {evalGrade && (
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
          (evalScore ?? 0) >= 0.9 ? 'bg-green-900/50 text-green-300'
            : (evalScore ?? 0) >= 0.7 ? 'bg-yellow-900/50 text-yellow-300'
            : 'bg-red-900/50 text-red-300'
        }`}>
          {evalGrade}
        </span>
      )}
    </button>
  )
}
