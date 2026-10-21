import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  History,
  FileText,
  Youtube,
  Trash2,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Filter,
  Eye,
} from 'lucide-react'
import { api } from '../api/client'
import { formatDate } from '../utils/helpers'

function ResultBadge({ result }) {
  if (result === 'credible') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/30">
        <CheckCircle2 className="h-3 w-3" /> Credible
      </span>
    )
  }
  if (result === 'suspicious') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-medium text-red-400 border border-red-500/30">
        <AlertTriangle className="h-3 w-3" /> Suspicious
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2.5 py-1 text-xs font-medium text-white/60 border border-white/20">
      <XCircle className="h-3 w-3" /> Error
    </span>
  )
}

export default function HistoryPanel({ refreshKey, onSelectItem }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    result: 'all',
    type: 'all',
    dateFrom: '',
    dateTo: '',
  })
  const [showFilters, setShowFilters] = useState(false)

  const loadHistory = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getHistory()
      setItems(data)
    } catch {
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadHistory()
  }, [loadHistory, refreshKey])

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (filters.result !== 'all' && item.result !== filters.result) return false
      if (filters.type !== 'all' && item.analysis_type !== filters.type) return false
      if (filters.dateFrom) {
        const from = new Date(filters.dateFrom)
        if (new Date(item.created_at) < from) return false
      }
      if (filters.dateTo) {
        const to = new Date(filters.dateTo)
        to.setHours(23, 59, 59, 999)
        if (new Date(item.created_at) > to) return false
      }
      return true
    })
  }, [items, filters])

  const handleDelete = async (id) => {
    try {
      await api.deleteHistory(id)
      setItems((prev) => prev.filter((item) => item.id !== id))
    } catch {
      /* ignore */
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <History className="h-5 w-5 text-indigo-400" />
            <h2 className="text-2xl font-semibold text-white">Analysis History</h2>
          </div>
          <p className="text-sm text-white/50">
            Browse past analyses stored in the database with full detailed metrics.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters((s) => !s)}
            className={`btn-ghost ${showFilters ? 'border-indigo-500/40 text-indigo-400' : ''}`}
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
          <button onClick={loadHistory} className="btn-ghost" disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="grid gap-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <label className="mb-1 block text-xs text-white/40">Result</label>
                <select
                  className="input-field"
                  value={filters.result}
                  onChange={(e) => setFilters({ ...filters, result: e.target.value })}
                >
                  <option value="all">All Results</option>
                  <option value="credible">Credible</option>
                  <option value="suspicious">Suspicious</option>
                  <option value="error">Error</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-white/40">Analysis Type</label>
                <select
                  className="input-field"
                  value={filters.type}
                  onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                >
                  <option value="all">All Types</option>
                  <option value="text">Text</option>
                  <option value="youtube">YouTube</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-white/40">From Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-white/40">To Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={filters.dateTo}
                  onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] py-16 text-center">
          <History className="mx-auto mb-4 h-12 w-12 text-white/20" />
          <p className="text-white/50">
            {items.length === 0 ? 'No analyses recorded yet.' : 'No items match your filters.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-xs text-white/40">{filteredItems.length} result(s) found</p>
          <AnimatePresence>
            {filteredItems.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.02 }}
                className="group rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 backdrop-blur-xl transition-all hover:border-indigo-500/30 hover:bg-white/[0.06]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/5">
                      {item.analysis_type === 'youtube' ? (
                        <Youtube className="h-4 w-4 text-red-400" />
                      ) : (
                        <FileText className="h-4 w-4 text-indigo-400" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-medium uppercase tracking-wider text-white/40">
                          {item.analysis_type === 'youtube' ? 'YouTube' : 'Text'} Analysis
                        </span>
                        <ResultBadge result={item.result} />
                        {item.confidence_score != null && (
                          <span className="rounded-md bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-300 border border-indigo-500/20">
                            {item.confidence_score}% Confidence
                          </span>
                        )}
                        {item.transcript_status && (
                          <span className="rounded-md bg-white/5 px-2 py-0.5 text-xs text-white/50 capitalize">
                            Status: {item.transcript_status.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                      <p className="mt-1.5 line-clamp-2 text-sm font-medium text-white/80">
                        {item.video_title || item.input_preview || item.youtube_url || '—'}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-white/40">
                        <span>{formatDate(item.created_at)}</span>
                        {item.word_count != null || item.transcript_length != null ? (
                          <span>{(item.word_count ?? item.transcript_length).toLocaleString()} words</span>
                        ) : null}
                      </div>
                      {item.youtube_url && (
                        <a
                          href={item.youtube_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-2 inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 truncate max-w-full"
                        >
                          <ExternalLink className="h-3 w-3 shrink-0" />
                          {item.youtube_url}
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2 border-t border-white/[0.06] pt-4">
                  <button
                    onClick={() => onSelectItem?.(item.id)}
                    className="btn-ghost text-xs"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    View Details
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="btn-ghost text-xs text-red-400 hover:border-red-500/30 hover:bg-red-500/10"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  )
}
