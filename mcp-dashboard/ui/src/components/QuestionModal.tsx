import { MessageSquare, X } from 'lucide-react'
import { useState } from 'react'
import { api } from '../api/client'
import type { Question } from '../types'
import { useDashboard } from '../context/DashboardContext'

type QuestionModalProps = {
  question: Question
  onClose: () => void
}

export function QuestionModal({ question, onClose }: QuestionModalProps) {
  const { refreshTasks, refreshStats } = useDashboard()
  const [answer, setAnswer] = useState('')
  const [selectedOption, setSelectedOption] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    const value = question.options ? selectedOption : answer.trim()
    if (!value) return

    setLoading(true)
    try {
      await api.answerQuestion(question.task_id, question.id, value)
      await refreshTasks()
      await refreshStats()
      onClose()
    } catch (err) {
      console.error('Failed to answer question:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="modal-backdrop animate-fade-in p-6"
      onClick={onClose}
    >
      <div
        className="modal-content w-full max-w-lg flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/15 border border-amber-500/20">
              <MessageSquare className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Question</h2>
              {question.agent && (
                <p className="text-xs text-gray-500 mt-0.5">From: {question.agent}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6">
          <p className="text-sm text-gray-200 mb-5 leading-relaxed whitespace-pre-wrap">
            {question.question}
          </p>

          {question.context && (
            <div className="bg-surface-850 border border-surface-700/50 rounded-xl p-4 mb-5 text-xs text-gray-400 max-h-36 overflow-y-auto whitespace-pre-wrap font-mono">
              {question.context}
            </div>
          )}

          {/* Answer input based on type */}
          {question.options ? (
            <div className="space-y-2 mb-5">
              {question.options.map(option => (
                <label
                  key={option}
                  className={`
                    flex items-center gap-3 p-4 rounded-xl border cursor-pointer
                    transition-all duration-200
                    ${selectedOption === option
                      ? 'border-accent-500/50 bg-accent-500/10 ring-1 ring-accent-500/30'
                      : 'border-surface-700 hover:border-surface-600 hover:bg-surface-800/50'
                    }
                  `}
                >
                  <input
                    type="radio"
                    name="option"
                    value={option}
                    checked={selectedOption === option}
                    onChange={() => setSelectedOption(option)}
                    className="w-4 h-4 text-accent-500 bg-surface-800 border-surface-600 focus:ring-accent-500/50"
                  />
                  <span className="text-sm text-gray-200">{option}</span>
                </label>
              ))}
            </div>
          ) : question.question_type === 'confirm' ? (
            <div className="flex gap-3 mb-5">
              <button
                onClick={() => setAnswer('yes')}
                className={`
                  flex-1 p-4 rounded-xl border text-sm font-medium
                  transition-all duration-200
                  ${answer === 'yes'
                    ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-500/30'
                    : 'border-surface-700 text-gray-300 hover:border-surface-600 hover:bg-surface-800/50'
                  }
                `}
              >
                Yes
              </button>
              <button
                onClick={() => setAnswer('no')}
                className={`
                  flex-1 p-4 rounded-xl border text-sm font-medium
                  transition-all duration-200
                  ${answer === 'no'
                    ? 'border-red-500/50 bg-red-500/10 text-red-300 ring-1 ring-red-500/30'
                    : 'border-surface-700 text-gray-300 hover:border-surface-600 hover:bg-surface-800/50'
                  }
                `}
              >
                No
              </button>
            </div>
          ) : (
            <textarea
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              placeholder="Type your answer..."
              rows={4}
              className="
                w-full bg-surface-850 border border-surface-700 rounded-xl
                px-4 py-3 text-sm text-white placeholder-gray-500
                resize-none mb-5 transition-all duration-200
                focus:outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20
              "
              autoFocus
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-5 border-t border-surface-800/50">
          <button
            onClick={onClose}
            className="px-5 py-2.5 text-sm font-medium text-gray-400 hover:text-white rounded-xl hover:bg-surface-800 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!(question.options ? selectedOption : answer.trim()) || loading}
            className="
              px-5 py-2.5 text-sm font-medium rounded-xl
              bg-gradient-to-r from-accent-600 to-accent-500 text-white
              shadow-glow-sm hover:from-accent-500 hover:to-accent-400
              disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
              transition-all duration-200 active:scale-[0.98]
            "
          >
            {loading ? 'Sending...' : 'Submit Answer'}
          </button>
        </div>
      </div>
    </div>
  )
}
