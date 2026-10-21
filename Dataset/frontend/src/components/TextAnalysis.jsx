import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Sparkles, Loader2 } from 'lucide-react'
import { api } from '../api/client'
import ResultCard from './ResultCard'
import GradientCard from './ui/GradientCard'

export default function TextAnalysis({ onAnalysisComplete }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const handleAnalyze = async () => {
    if (!text.trim()) {
      setError('Please enter some text.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const data = await api.analyzeText(text)
      setResult(data)
      onAnalysisComplete?.()
    } catch (err) {
      setError(typeof err.data?.detail === 'string' ? err.data.detail : err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div>
        <div className="mb-2 flex items-center gap-2">
          <FileText className="h-5 w-5 text-indigo-400" />
          <h2 className="text-2xl font-semibold text-white">Text Analysis</h2>
        </div>
        <p className="text-sm text-white/50">
          Paste any text content to detect credibility using TF-IDF + LinearSVC classification.
        </p>
      </div>

      <GradientCard hover={false}>
        <label className="mb-2 block text-sm font-medium text-white/70">Enter Text</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste article, review, or any text content here..."
          rows={8}
          className="input-field resize-none"
        />

        {error && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-3 text-sm text-red-400"
          >
            {error}
          </motion.p>
        )}

        <div className="mt-4 flex justify-end">
          <button onClick={handleAnalyze} disabled={loading} className="btn-primary">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Analyze Text
              </>
            )}
          </button>
        </div>
      </GradientCard>

      {result && (
        <ResultCard
          result={result.result}
          label={result.label}
          confidenceScore={result.confidence_score}
          riskLevel={result.risk_level}
          recommendation={result.recommendation}
          wordCount={result.word_count}
          characterCount={result.character_count}
          indicators={result.indicators}
          historyId={result.history_id}
          inputPreview={text.slice(0, 500)}
          fullContent={text}
          createdAt={new Date().toISOString()}
        />
      )}
    </motion.div>
  )
}
