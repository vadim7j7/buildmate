import { MessageSquare, X } from 'lucide-react'
import { useState } from 'react'
import { api } from '../api/client'
import type { Question } from '../types'
import { useDashboard } from '../context/DashboardContext'

interface Props {
  question: Question
  onClose: () => void
}

export function QuestionModal({ question, onClose }: Props) {
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
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold text-white">Question</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {question.agent && (
          <p className="text-xs text-gray-500 mb-2">From: {question.agent}</p>
        )}

        <p className="text-sm text-gray-200 mb-4 whitespace-pre-wrap">{question.question}</p>

        {question.context && (
          <div className="bg-gray-800 rounded-lg p-3 mb-4 text-xs text-gray-400 max-h-32 overflow-y-auto whitespace-pre-wrap">
            {question.context}
          </div>
        )}

        {/* Answer input based on type */}
        {question.options ? (
          <div className="space-y-2 mb-4">
            {question.options.map(option => (
              <label
                key={option}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedOption === option
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <input
                  type="radio"
                  name="option"
                  value={option}
                  checked={selectedOption === option}
                  onChange={() => setSelectedOption(option)}
                  className="text-blue-500 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-200">{option}</span>
              </label>
            ))}
          </div>
        ) : question.question_type === 'confirm' ? (
          <div className="flex gap-3 mb-4">
            <button
              onClick={() => { setAnswer('yes'); }}
              className={`flex-1 p-3 rounded-lg border text-sm transition-colors ${
                answer === 'yes' ? 'border-green-500 bg-green-500/10 text-green-300' : 'border-gray-700 text-gray-300 hover:border-gray-600'
              }`}
            >
              Yes
            </button>
            <button
              onClick={() => { setAnswer('no'); }}
              className={`flex-1 p-3 rounded-lg border text-sm transition-colors ${
                answer === 'no' ? 'border-red-500 bg-red-500/10 text-red-300' : 'border-gray-700 text-gray-300 hover:border-gray-600'
              }`}
            >
              No
            </button>
          </div>
        ) : (
          <textarea
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            placeholder="Type your answer..."
            rows={3}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none mb-4"
            autoFocus
          />
        )}

        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!(question.options ? selectedOption : answer.trim()) || loading}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            {loading ? 'Sending...' : 'Submit Answer'}
          </button>
        </div>
      </div>
    </div>
  )
}
