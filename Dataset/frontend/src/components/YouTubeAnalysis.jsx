import { useState } from 'react'
import { motion } from 'framer-motion'
import { Youtube, ExternalLink, Sparkles, Loader2, AlertCircle, Play, FileText, Link2 } from 'lucide-react'
import { api } from '../api/client'
import ResultCard from './ResultCard'
import GradientCard from './ui/GradientCard'

export default function YouTubeAnalysis({ onAnalysisComplete }) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const handleAnalyze = async () => {
    if (!url.trim()) {
      setError({ message: 'Please enter a YouTube URL.' })
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await api.analyzeYouTube(url)
      setResult({ ...data, youtube_url: data.youtube_url || url })
      onAnalysisComplete?.()
    } catch (err) {
      const detail = err.data?.detail
      if (typeof detail === 'object') {
        setError(detail)
        onAnalysisComplete?.()
      } else {
        setError({ message: typeof detail === 'string' ? detail : err.message })
      }
    } finally {
      setLoading(false)
    }
  }

  const statusConfig = {
    available: { label: 'Transcript Available', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
    removed: { label: 'Video Removed', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
    unavailable: { label: 'Transcript Not Available', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
    disabled: { label: 'Transcripts Disabled', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
    failed: { label: 'Analysis Failed', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
    invalid: { label: 'Invalid URL', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
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
          <Youtube className="h-5 w-5 text-red-400" />
          <h2 className="text-2xl font-semibold text-white">YouTube Analysis</h2>
        </div>
        <p className="text-sm text-white/50">
          Analyze video transcripts for credibility. Captions are fetched automatically.
        </p>
      </div>

      <GradientCard hover={false}>
        <label className="mb-2 block text-sm font-medium text-white/70">Video URL</label>
        <div className="relative">
          <Link2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/..."
            className="input-field pl-10"
          />
        </div>

        <div className="mt-4 flex justify-end">
          <button onClick={handleAnalyze} disabled={loading} className="btn-primary">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Fetching Transcript...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Analyze Video
              </>
            )}
          </button>
        </div>
      </GradientCard>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <GradientCard hover={false} className={`border ${statusConfig[error.transcript_status]?.bg || 'border-red-500/20'}`}>
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
              <div>
                <p className={`font-semibold ${statusConfig[error.transcript_status]?.color || 'text-red-400'}`}>
                  {statusConfig[error.transcript_status]?.label || error.error_message || error.message}
                </p>
                {error.detail && typeof error.detail === 'string' && (
                  <p className="mt-2 text-sm text-white/50">{error.detail}</p>
                )}
                {error.error_detail && (
                  <p className="mt-2 text-sm text-white/50">{error.error_detail}</p>
                )}
              </div>
            </div>
          </GradientCard>
        </motion.div>
      )}

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <GradientCard delay={0.1}>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-white/40">
              Video Details
            </h3>
            <div className="space-y-4">
              {result.video_title && (
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-500/10">
                    <Play className="h-4 w-4 text-red-400" />
                  </div>
                  <div>
                    <p className="text-xs text-white/40">Video Title</p>
                    <p className="mt-0.5 font-medium text-white">{result.video_title}</p>
                  </div>
                </div>
              )}

              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/5">
                  <Link2 className="h-4 w-4 text-indigo-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-white/40">Video URL</p>
                  <a
                    href={result.youtube_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-0.5 block truncate text-sm text-indigo-400 hover:text-indigo-300"
                  >
                    {result.youtube_url}
                  </a>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className={`rounded-xl border p-3 ${
                  result.transcript_status === 'whisper_generated' ? 'bg-purple-500/10 border-purple-500/20' :
                  result.transcript_status === 'available' ? statusConfig.available.bg : statusConfig.unavailable.bg
                }`}>
                  <p className="text-xs text-white/40">Transcript Status</p>
                  <p className={`mt-0.5 text-sm font-medium ${
                    result.transcript_status === 'whisper_generated' ? 'text-purple-400' :
                    result.transcript_status === 'available' ? statusConfig.available.color : statusConfig.unavailable.color
                  }`}>
                    {result.transcript_status === 'whisper_generated' ? 'Whisper-Generated' : 
                     result.transcript_status === 'available' ? 'Available' : 'Unavailable'}
                  </p>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                  <p className="text-xs text-white/40">Transcript Length</p>
                  <p className="mt-0.5 flex items-center gap-1.5 text-sm font-medium text-white">
                    <FileText className="h-3.5 w-3.5 text-white/40" />
                    {result.word_count?.toLocaleString() || result.transcript_length?.toLocaleString()} words
                  </p>
                </div>
              </div>
            </div>
          </GradientCard>

          <ResultCard
            result={result.result}
            label={result.label}
            confidenceScore={result.confidence_score}
            riskLevel={result.risk_level}
            recommendation={result.recommendation}
            indicators={result.indicators}
            historyId={result.history_id}
            transcriptStatus={result.transcript_status}
            transcriptLength={result.transcript_length}
            wordCount={result.word_count}
            characterCount={result.character_count}
            videoTitle={result.video_title}
            youtubeUrl={result.youtube_url}
            inputPreview={result.input_preview}
            createdAt={new Date().toISOString()}
          />

          {result.youtube_url && (
            <motion.a
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              href={result.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary inline-flex w-full justify-center sm:w-auto"
            >
              <ExternalLink className="h-4 w-4" />
              Watch Original Video
            </motion.a>
          )}
        </motion.div>
      )}
    </motion.div>
  )
}
