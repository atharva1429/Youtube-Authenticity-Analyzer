import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react'
import { motion } from 'framer-motion'
import {
  Printer,
  Download,
  ArrowLeft,
  ShieldAlert,
  Loader2,
  FileWarning,
  Copy,
  Share2,
  Check,
} from 'lucide-react'
import { api } from '../api/client'
import { formatDate, REPORT_REASONS } from '../utils/helpers'
import { generateAnalysisPdf } from '../utils/pdfReport'
import { useAuth } from '../context/AuthContext'
import AuroraBackground from '../components/ui/AuroraBackground'

export default function ReportPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [detail, setDetail] = useState(null)
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [showReportForm, setShowReportForm] = useState(false)
  const [form, setForm] = useState({ reporter_name: '', reason: REPORT_REASONS[0], comments: '' })
  const [submitting, setSubmitting] = useState(false)
  const [copied, setCopied] = useState(false)
  const [shared, setShared] = useState(false)

  useEffect(() => {
    if (user?.username) {
      setForm((f) => ({ ...f, reporter_name: user.username }))
    }
  }, [user])

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      api.getHistoryDetail(id),
      api.getReports().catch(() => []),
    ])
      .then(([d, allReports]) => {
        setDetail(d)
        setReports(allReports.filter((r) => r.analysis_id === Number(id)))
      })
      .catch(() => setDetail(null))
      .finally(() => setLoading(false))
  }, [id])

  const handlePrint = () => window.print()

  const handleDownloadPdf = () => {
    if (detail) generateAnalysisPdf(detail)
  }

  const handleCopyReport = async () => {
    if (!detail) return
    const textReport = `YouTube Authenticity Analyzer — Suspicious Content Report
==================================================
Analysis ID: #${detail.id}
Date/Time: ${formatDate(detail.created_at)}
Analysis Type: ${detail.analysis_type}
Prediction: ${detail.result === 'credible' ? 'Credible Content' : 'Suspicious Content'}
Confidence Score: ${detail.confidence_score != null ? detail.confidence_score + '%' : 'N/A'}
Risk Level: ${detail.risk_level || 'High Risk'}
Recommendation: ${detail.recommendation || 'Suspicious content detected by the model. Further verification from reliable sources is recommended.'}
Original URL: ${detail.youtube_url || 'N/A'}
Indicators Found: ${detail.indicators?.join(', ') || 'None'}
==================================================
Excerpt:
${(detail.full_content || detail.input_preview || '').slice(0, 500)}
`
    try {
      await navigator.clipboard.writeText(textReport)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* ignore */
    }
  }

  const handleShareReport = async () => {
    const shareUrl = window.location.href
    if (navigator.share) {
      try {
        await navigator.share({
          title: `YouTube Authenticity Report #${id}`,
          text: `Suspicious content analysis report for Analysis #${id}`,
          url: shareUrl,
        })
      } catch {
        /* ignore */
      }
    } else {
      try {
        await navigator.clipboard.writeText(shareUrl)
        setShared(true)
        setTimeout(() => setShared(false), 2000)
      } catch {
        /* ignore */
      }
    }
  }

  const handleSubmitReport = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.createReport({ analysis_id: Number(id), ...form })
      const allReports = await api.getReports()
      setReports(allReports.filter((r) => r.analysis_id === Number(id)))
      setShowReportForm(false)
    } catch {
      /* ignore */
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <AuroraBackground className="flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
      </AuroraBackground>
    )
  }

  if (!detail || detail.result !== 'suspicious') {
    return (
      <AuroraBackground className="flex flex-col items-center justify-center gap-4 p-8">
        <p className="text-white/60">Report not available for this analysis.</p>
        <button onClick={() => navigate('/dashboard')} className="btn-primary">
          Back to Dashboard
        </button>
      </AuroraBackground>
    )
  }

  const reportReasons = reports.map((r) => r.reason)
  const allReasons = [...new Set([...(detail.indicators || []), ...reportReasons])]

  return (
    <AuroraBackground>
      <div className="no-print mx-auto max-w-4xl px-4 py-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <button onClick={() => navigate('/dashboard')} className="btn-ghost">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </button>
          <div className="flex flex-wrap gap-2">
            <button onClick={handleCopyReport} className="btn-ghost text-xs">
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
              {copied ? 'Copied Report!' : 'Copy Report'}
            </button>
            <button onClick={handleShareReport} className="btn-ghost text-xs">
              {shared ? <Check className="h-4 w-4 text-emerald-400" /> : <Share2 className="h-4 w-4" />}
              {shared ? 'Link Copied!' : 'Share Report'}
            </button>
            <button onClick={handlePrint} className="btn-ghost text-xs">
              <Printer className="h-4 w-4" />
              Print
            </button>
            <button onClick={handleDownloadPdf} className="btn-primary text-xs">
              <Download className="h-4 w-4" />
              Download Report
            </button>
            {!detail.reported && (
              <button onClick={() => setShowReportForm(true)} className="btn-ghost border-amber-500/30 text-amber-400 text-xs">
                <FileWarning className="h-4 w-4" />
                Report Suspicious Content
              </button>
            )}
          </div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        id="suspicious-report"
        className="report-document mx-auto max-w-4xl px-4 pb-16"
      >
        <div className="overflow-hidden rounded-2xl border border-red-500/20 bg-[#0c0c14]/90 shadow-2xl backdrop-blur-xl print:border print:border-gray-300 print:bg-white print:shadow-none">
          {/* Header */}
          <div className="border-b border-red-500/20 bg-gradient-to-r from-red-500/10 to-orange-500/5 px-8 py-6 print:border-gray-200 print:bg-gray-50">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-red-500/20 print:bg-red-100">
                <ShieldAlert className="h-7 w-7 text-red-400 print:text-red-600" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-red-400/80 print:text-red-600">
                  Report Suspicious Content
                </p>
                <h1 className="mt-1 text-2xl font-bold text-white print:text-gray-900">
                  YouTube Authenticity Analyzer
                </h1>
                <p className="mt-1 text-sm text-white/50 print:text-gray-500">
                  Automated content credibility assessment report
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-6 px-8 py-6 print:text-gray-800">
            {/* Meta grid */}
            <div className="grid gap-4 sm:grid-cols-2">
              <ReportField label="Analysis ID" value={`#${detail.id}`} />
              <ReportField label="Date / Time" value={formatDate(detail.created_at)} />
              <ReportField label="Analysis Type" value={detail.analysis_type} capitalize />
              <ReportField
                label="Prediction"
                value="Suspicious Content ⚠️"
                highlight="text-red-400 print:text-red-600 font-bold"
              />
              <ReportField label="Confidence Score" value={detail.confidence_score != null ? `${detail.confidence_score}%` : 'N/A'} />
              <ReportField label="Risk Level" value={detail.risk_level || 'High Risk'} highlight="text-red-300 print:text-red-700 font-semibold" />
              <ReportField label="Word Count" value={`${(detail.word_count ?? detail.transcript_length ?? 0).toLocaleString()} words`} />
              <ReportField label="Character Count" value={`${(detail.character_count ?? 0).toLocaleString()} characters`} />
            </div>

            {/* Recommendation Box */}
            <section className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 print:border-red-300 print:bg-red-50">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-red-300 print:text-red-800">
                Recommendation
              </h2>
              <p className="mt-1 text-sm text-red-100 print:text-red-900 font-medium">
                {detail.recommendation || 'Suspicious content detected by the model. Further verification from reliable sources is recommended.'}
              </p>
            </section>

            {detail.video_title && (
              <ReportField label="Video Title" value={detail.video_title} full />
            )}

            {detail.youtube_url && (
              <ReportField label="Original YouTube URL" value={detail.youtube_url} full link />
            )}

            {/* Risk Indicators */}
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-white/50 print:text-gray-500">
                Risk Indicators Found
              </h2>
              {detail.indicators?.length > 0 ? (
                <ul className="space-y-2">
                  {detail.indicators.map((ind) => (
                    <li
                      key={ind}
                      className="flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-2.5 text-sm text-amber-100 print:border-amber-200 print:bg-amber-50 print:text-amber-900"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                      {ind}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-white/40 print:text-gray-500">No specific text indicators detected.</p>
              )}
            </section>

            {/* Reasons Triggered */}
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-white/50 print:text-gray-500">
                Reasons Triggered
              </h2>
              <ul className="space-y-2">
                <li className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-2.5 text-sm text-red-200 print:border-red-200 print:bg-red-50 print:text-red-800">
                  Suspicious content detected by the model (TF-IDF + LinearSVC)
                </li>
                {allReasons.map((reason) => (
                  <li
                    key={reason}
                    className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-white/70 print:border-gray-200 print:bg-gray-50 print:text-gray-700"
                  >
                    {reason}
                  </li>
                ))}
              </ul>
            </section>

            {/* Content excerpt */}
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-white/50 print:text-gray-500">
                Analyzed Content / Transcript
              </h2>
              <div className="max-h-48 overflow-y-auto rounded-lg border border-white/10 bg-white/[0.02] p-4 text-sm leading-relaxed text-white/70 print:border-gray-200 print:bg-gray-50 print:text-gray-700">
                {(detail.full_content || detail.input_preview || '').slice(0, 1500)}
                {(detail.full_content || detail.input_preview || '').length > 1500 && '...'}
              </div>
            </section>

            {reports.length > 0 && (
              <section>
                <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-white/50 print:text-gray-500">
                  Filed User Reports
                </h2>
                {reports.map((r) => (
                  <div key={r.id} className="mb-2 rounded-lg border border-white/10 p-3 text-sm print:border-gray-200">
                    <p className="font-medium text-white print:text-gray-900">{r.reason}</p>
                    <p className="text-white/50 print:text-gray-500">By {r.reporter_name} · {formatDate(r.created_at)}</p>
                    {r.comments && <p className="mt-1 text-white/60 print:text-gray-600">{r.comments}</p>}
                  </div>
                ))}
              </section>
            )}

            <footer className="border-t border-white/10 pt-4 text-xs text-white/40 print:border-gray-200 print:text-gray-500">
              YouTube Authenticity Analyzer · Suspicious content detected by the model. Further verification from reliable sources is recommended.
            </footer>
          </div>
        </div>
      </motion.div>

      {/* Report filing modal */}
      {showReportForm && (
        <div className="no-print fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0c0c14] p-6">
            <h3 className="mb-4 text-lg font-semibold text-white">File Suspicious Content Report</h3>
            <form onSubmit={handleSubmitReport} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm text-white/60">Your Name</label>
                <input
                  className="input-field"
                  value={form.reporter_name}
                  onChange={(e) => setForm({ ...form, reporter_name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-white/60">Reason</label>
                <select
                  className="input-field"
                  value={form.reason}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}
                >
                  {REPORT_REASONS.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm text-white/60">Comments (optional)</label>
                <textarea
                  className="input-field resize-none"
                  rows={3}
                  value={form.comments}
                  onChange={(e) => setForm({ ...form, comments: e.target.value })}
                />
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={() => setShowReportForm(false)} className="btn-ghost flex-1">
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="btn-primary flex-1">
                  {submitting ? 'Submitting...' : 'Submit Report'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AuroraBackground>
  )
}

function ReportField({ label, value, capitalize, highlight, full, link }) {
  return (
    <div className={full ? 'sm:col-span-2' : ''}>
      <p className="text-xs font-medium uppercase tracking-wider text-white/40 print:text-gray-500">{label}</p>
      {link ? (
        <a href={value} target="_blank" rel="noopener noreferrer" className="mt-0.5 block break-all text-sm text-indigo-400 print:text-blue-600">
          {value}
        </a>
      ) : (
        <p className={`mt-0.5 text-sm font-medium text-white print:text-gray-900 ${capitalize ? 'capitalize' : ''} ${highlight || ''}`}>
          {value}
        </p>
      )}
    </div>
  )
}
