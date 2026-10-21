import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  FileText,
  Youtube,
  Calendar,
  Hash,
  ExternalLink,
  Download,
  FileWarning,
  Loader2,
  Database,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, downloadExport } from '../api/client'
import { formatDate } from '../utils/helpers'
import { generateAnalysisPdf } from '../utils/pdfReport'
import IndicatorsPanel from './IndicatorsPanel'

function ResultBadge({ result }) {
  const styles = {
    credible: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    suspicious: 'bg-red-500/15 text-red-400 border-red-500/30',
    error: 'bg-white/10 text-white/60 border-white/20',
  }
  const labels = { credible: 'Credible Content ✅', suspicious: 'Suspicious Content ⚠️', error: 'Error' }
  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${styles[result] || styles.error}`}>
      {labels[result] || result}
    </span>
  )
}

export default function HistoryDetailModal({ itemId, onClose }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!itemId) {
      setDetail(null)
      setError('')
      return
    }

    let cancelled = false
    setLoading(true)
    setError('')
    setDetail(null)

    api
      .getHistoryDetail(itemId)
      .then((data) => {
        if (!cancelled) setDetail(data)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || 'Could not load analysis details.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [itemId])

  useEffect(() => {
    const handleKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  const words = detail?.word_count ?? detail?.transcript_length ?? (detail?.full_content ? detail.full_content.split(/\s+/).length : 0)
  const chars = detail?.character_count ?? (detail?.full_content ? detail.full_content.length : 0)

  return (
    <AnimatePresence>
      {itemId && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-black/75 backdrop-blur-md" />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
            className="relative flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0c0c14] shadow-2xl backdrop-blur-xl"
          >
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20">
                  {detail?.analysis_type === 'youtube' ? (
                    <Youtube className="h-5 w-5 text-red-400" />
                  ) : (
                    <FileText className="h-5 w-5 text-indigo-400" />
                  )}
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-white">Analysis Details</h2>
                  <p className="text-xs text-white/40">Analysis #{itemId}</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-2 text-white/50 transition-colors hover:bg-white/10 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-5">
              {loading ? (
                <div className="flex justify-center py-16">
                  <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
                </div>
              ) : error ? (
                <p className="py-8 text-center text-red-400">{error}</p>
              ) : detail ? (
                <div className="space-y-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <ResultBadge result={detail.result} />
                    <span className="rounded-lg bg-white/5 px-2.5 py-1 text-xs font-medium uppercase tracking-wider text-white/50">
                      {detail.analysis_type} Analysis
                    </span>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <MetaItem icon={Hash} label="Analysis ID" value={`#${detail.id}`} />
                    <MetaItem icon={Calendar} label="Date / Time" value={formatDate(detail.created_at)} />
                    <MetaItem
                      icon={ShieldAlert}
                      label="Risk Level"
                      value={detail.risk_level || (detail.result === 'credible' ? 'Low Risk' : 'High Risk')}
                    />
                    <MetaItem
                      icon={ShieldCheck}
                      label="Confidence Score"
                      value={detail.confidence_score != null ? `${detail.confidence_score}%` : 'N/A'}
                    />
                    <MetaItem
                      icon={FileText}
                      label="Word Count"
                      value={`${words.toLocaleString()} words`}
                    />
                    <MetaItem
                      icon={FileText}
                      label="Character Count"
                      value={`${chars.toLocaleString()} characters`}
                    />
                  </div>

                  {detail.youtube_url && (
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs font-medium uppercase tracking-wider text-white/40">Original YouTube URL</p>
                      <a
                        href={detail.youtube_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 inline-flex items-center gap-2 break-all text-sm text-indigo-400 hover:text-indigo-300"
                      >
                        <ExternalLink className="h-4 w-4 shrink-0" />
                        {detail.youtube_url}
                      </a>
                    </div>
                  )}

                  {detail.video_title && (
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs font-medium uppercase tracking-wider text-white/40">Video Title</p>
                      <p className="mt-1 text-sm font-medium text-white">{detail.video_title}</p>
                    </div>
                  )}

                  {detail.recommendation && (
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs font-medium uppercase tracking-wider text-white/40">Recommendation</p>
                      <p className="mt-1 text-sm text-white/80">{detail.recommendation}</p>
                    </div>
                  )}

                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="mb-2 text-xs font-medium uppercase tracking-wider text-white/40">Original Content / Transcript</p>
                    <p className="max-h-48 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-white/75">
                      {detail.full_content || detail.input_preview || 'No content available.'}
                    </p>
                  </div>

                  {detail.indicators?.length > 0 && (
                    <IndicatorsPanel indicators={detail.indicators} />
                  )}
                </div>
              ) : null}
            </div>

            {detail && (
              <div className="flex flex-wrap gap-2 border-t border-white/10 px-6 py-4">
                {detail.result === 'suspicious' && (
                  <Link
                    to={`/report/${detail.id}`}
                    className="btn-primary text-xs"
                    onClick={onClose}
                  >
                    <FileWarning className="h-4 w-4" />
                    Full Report
                  </Link>
                )}
                <button
                  onClick={() => generateAnalysisPdf(detail)}
                  className="btn-ghost text-xs"
                >
                  <Download className="h-4 w-4" />
                  Download PDF
                </button>
                <button
                  onClick={() => downloadExport(api.exportJson(detail.id), `analysis-${detail.id}.json`)}
                  className="btn-ghost text-xs"
                >
                  <Download className="h-4 w-4" />
                  Export JSON
                </button>
                {detail.youtube_url && (
                  <a href={detail.youtube_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs">
                    <ExternalLink className="h-4 w-4" />
                    Watch Video
                  </a>
                )}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function MetaItem({ icon: Icon, label, value, capitalize }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" />
      <div>
        <p className="text-xs text-white/40">{label}</p>
        <p className={`text-sm font-medium text-white ${capitalize ? 'capitalize' : ''}`}>{value}</p>
      </div>
    </div>
  )
}
