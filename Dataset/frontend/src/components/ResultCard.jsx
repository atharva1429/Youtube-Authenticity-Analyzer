import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  CheckCircle2,
  AlertTriangle,
  FileWarning,
  ExternalLink,
  Copy,
  Download,
  Check,
  Shield,
  FileText,
} from 'lucide-react'
import IndicatorsPanel from './IndicatorsPanel'
import { generateAnalysisPdf } from '../utils/pdfReport'

export default function ResultCard({
  result,
  label,
  indicators = [],
  historyId,
  confidenceScore,
  riskLevel,
  recommendation,
  transcriptStatus,
  transcriptLength,
  wordCount,
  characterCount,
  videoTitle,
  youtubeUrl,
  fullContent,
  inputPreview,
  createdAt,
}) {
  const [copied, setCopied] = useState(false)
  const isCredible = result === 'credible'
  const displayWords = wordCount ?? transcriptLength ?? (fullContent ? fullContent.split(/\s+/).length : 0)
  const displayChars = characterCount ?? (fullContent ? fullContent.length : 0)

  const handleCopyUrl = async () => {
    const url = youtubeUrl || window.location.href
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* ignore */
    }
  }

  const handleDownloadReport = () => {
    generateAnalysisPdf({
      id: historyId,
      result,
      created_at: createdAt || new Date().toISOString(),
      analysis_type: youtubeUrl ? 'youtube' : 'text',
      transcript_status: transcriptStatus,
      transcript_length: displayWords,
      youtube_url: youtubeUrl,
      full_content: fullContent,
      input_preview: inputPreview,
      indicators,
      confidence_score: confidenceScore,
      risk_level: riskLevel,
      recommendation,
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={`relative overflow-hidden rounded-2xl border p-6 backdrop-blur-xl ${
        isCredible
          ? 'border-emerald-500/30 bg-emerald-500/5'
          : 'border-red-500/30 bg-red-500/5'
      }`}
    >
      <div className="flex items-start gap-4">
        <div
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${
            isCredible ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
          }`}
        >
          {isCredible ? <CheckCircle2 className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs font-medium uppercase tracking-wider text-white/40">Analysis Result</p>
            {riskLevel && (
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                isCredible ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'
              }`}>
                {riskLevel}
              </span>
            )}
          </div>
          <h3 className={`mt-1 text-xl font-bold ${isCredible ? 'text-emerald-400' : 'text-red-400'}`}>
            {label}
          </h3>

          {videoTitle && (
            <p className="mt-2 text-sm font-medium text-white/80">{videoTitle}</p>
          )}

          {/* Key Metrics Grid */}
          <div className="mt-4 grid gap-3 sm:grid-cols-3 border-t border-white/10 pt-4">
            {confidenceScore != null && (
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                <span className="text-xs text-white/40 block">Confidence Score</span>
                <span className="text-lg font-bold text-white">{confidenceScore}%</span>
              </div>
            )}
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
              <span className="text-xs text-white/40 block">Word Count</span>
              <span className="text-lg font-bold text-white">{displayWords.toLocaleString()}</span>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
              <span className="text-xs text-white/40 block">Character Count</span>
              <span className="text-lg font-bold text-white">{displayChars.toLocaleString()}</span>
            </div>
          </div>

          {/* Recommendation */}
          {recommendation && (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] p-3">
              <span className="text-xs font-medium uppercase text-white/40 block">Recommendation</span>
              <p className="mt-1 text-sm text-white/80">{recommendation}</p>
            </div>
          )}

          {!isCredible && indicators.length > 0 && (
            <IndicatorsPanel indicators={indicators} compact />
          )}

          {!isCredible && (
            <div className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <p className="flex items-center gap-2 text-sm font-semibold text-red-300">
                <AlertTriangle className="h-4 w-4" />
                Suspicious Content Detected
              </p>
              <p className="mt-1 text-xs text-red-200/70">
                Suspicious content detected by the model. Further verification from reliable sources is recommended.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {youtubeUrl && (
                  <a
                    href={youtubeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-ghost text-xs text-red-200 hover:border-red-500/30 hover:bg-red-500/20"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    Open Original Video
                  </a>
                )}
                <button onClick={handleCopyUrl} className="btn-ghost text-xs text-red-200 hover:border-red-500/30 hover:bg-red-500/20">
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? 'Copied!' : 'Copy Link'}
                </button>
                <button onClick={handleDownloadReport} className="btn-ghost text-xs text-red-200 hover:border-red-500/30 hover:bg-red-500/20">
                  <Download className="h-3.5 w-3.5" />
                  Download Report
                </button>
                {historyId && (
                  <Link
                    to={`/report/${historyId}`}
                    className="btn-ghost text-xs text-red-200 hover:border-red-500/30 hover:bg-red-500/20"
                  >
                    <FileWarning className="h-3.5 w-3.5" />
                    Full Report
                  </Link>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
