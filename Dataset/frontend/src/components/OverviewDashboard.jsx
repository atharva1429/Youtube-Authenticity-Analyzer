import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  FileText,
  Youtube,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Server,
  Zap,
  TrendingUp,
  ChevronRight,
  Sparkles,
  CalendarDays,
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import { api } from '../api/client'
import { formatDate } from '../utils/helpers'
import GradientCard from './ui/GradientCard'
import AnimatedCounter from './ui/AnimatedCounter'

const PIE_COLORS = ['#22c55e', '#ef4444', '#64748b']

const tooltipStyle = {
  backgroundColor: 'rgba(12,12,20,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '12px',
  color: '#fff',
}

function ResultBadge({ result }) {
  const isCredible = result === 'credible'
  const isSuspicious = result === 'suspicious'
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium border ${
        isCredible
          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
          : isSuspicious
            ? 'bg-red-500/10 text-red-400 border-red-500/30'
            : 'bg-white/10 text-white/50 border-white/20'
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${isCredible ? 'bg-emerald-400' : isSuspicious ? 'bg-red-400' : 'bg-slate-400'}`} />
      {isCredible ? 'Credible' : isSuspicious ? 'Suspicious' : 'Error'}
    </span>
  )
}

export default function OverviewDashboard({ refreshKey = 0, onNavigate, onOpenHistory }) {
  const [stats, setStats] = useState(null)
  const [history, setHistory] = useState([])
  const [health, setHealth] = useState(null)
  const [trends, setTrends] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    try {
      const [s, h, healthData, trendData] = await Promise.all([
        api.getStats(),
        api.getHistory(),
        api.getHealth().catch(() => null),
        api.getAnalyticsTrends().catch(() => null),
      ])
      setStats(s)
      setHistory(h.slice(0, 6))
      setHealth(healthData)
      setTrends(trendData)
    } catch {
      setStats(null)
      setHistory([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData, refreshKey])

  const resultChartData = useMemo(
    () =>
      [
        { name: 'Credible', value: stats?.credible_results ?? 0, fill: PIE_COLORS[0] },
        { name: 'Suspicious', value: stats?.suspicious_results ?? 0, fill: PIE_COLORS[1] },
        { name: 'Errors', value: stats?.error_results ?? 0, fill: PIE_COLORS[2] },
      ].filter((d) => d.value > 0),
    [stats],
  )

  const crediblePct = stats?.total_analyses
    ? Math.round((stats.credible_results / stats.total_analyses) * 100)
    : 0
  const suspiciousPct = stats?.total_analyses
    ? Math.round((stats.suspicious_results / stats.total_analyses) * 100)
    : 0

  const statCards = [
    { label: 'Total Analyses', value: stats?.total_analyses ?? 0, icon: Activity, accent: 'from-indigo-500/20 to-indigo-500/5' },
    { label: 'Credible Content', value: stats?.credible_results ?? 0, icon: ShieldCheck, accent: 'from-emerald-500/20 to-emerald-500/5' },
    { label: 'Suspicious Content', value: stats?.suspicious_results ?? 0, icon: ShieldAlert, accent: 'from-red-500/20 to-red-500/5' },
    { label: 'YouTube Analyses', value: stats?.youtube_analyses ?? 0, icon: Youtube, accent: 'from-red-500/20 to-red-500/5' },
    { label: 'Text Analyses', value: stats?.text_analyses ?? 0, icon: FileText, accent: 'from-cyan-500/20 to-cyan-500/5' },
    { label: "Today's Analyses", value: stats?.today_analyses ?? 0, icon: CalendarDays, accent: 'from-violet-500/20 to-violet-500/5' },
  ]

  const healthRows = [
    {
      label: 'API Server',
      value: (health?.status === 'online' || health?.api_server === 'online') ? 'Online' : health ? 'Offline' : 'Checking...',
      ok: health?.status === 'online' || health?.api_server === 'online',
    },
    {
      label: 'ML Model',
      value: health?.model_loaded === true ? 'Loaded (LinearSVC)' : health ? 'Not Loaded' : 'Checking...',
      ok: health?.model_loaded === true,
    },
    {
      label: 'TF-IDF Vectorizer',
      value: health?.vectorizer_loaded === true ? 'Loaded' : health ? 'Not Loaded' : 'Checking...',
      ok: health?.vectorizer_loaded === true,
    },
    {
      label: 'Database',
      value: health?.database_connected === true ? 'Connected (SQLite)' : health ? 'Disconnected' : 'Checking...',
      ok: health?.database_connected === true,
    },
  ]


  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-indigo-500/10 via-violet-500/5 to-transparent p-8 backdrop-blur-xl">
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-indigo-500/20 blur-[80px]" />
        <div className="relative">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
            <Sparkles className="h-3.5 w-3.5" />
            AI-Powered Content Authenticity Analysis Dashboard
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            YouTube Authenticity Analyzer
          </h2>
          <p className="mt-3 max-w-2xl text-sm text-white/50 md:text-base">
            Verify authenticity across YouTube transcripts and text content using TF-IDF + LinearSVC machine learning models, deterministic confidence scoring, and detailed reporting.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button onClick={() => onNavigate?.('youtube')} className="btn-primary text-sm">
              <Youtube className="h-4 w-4" />
              Analyze YouTube
            </button>
            <button onClick={() => onNavigate?.('text')} className="btn-ghost text-sm">
              <FileText className="h-4 w-4" />
              Analyze Text
            </button>
          </div>
        </div>
      </section>

      {/* Statistics Cards */}
      <section>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {statCards.map((card, i) => {
            const Icon = card.icon
            return (
              <GradientCard key={card.label} delay={i * 0.05}>
                <div className={`absolute inset-0 bg-gradient-to-br ${card.accent} opacity-50`} />
                <div className="relative flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold text-white">
                      <AnimatedCounter value={card.value} />
                    </p>
                    <p className="mt-1 text-sm text-white/50">{card.label}</p>
                  </div>
                  <div className="rounded-xl bg-white/5 p-3 transition-transform duration-300 group-hover:scale-110">
                    <Icon className="h-6 w-6 text-white/70" />
                  </div>
                </div>
              </GradientCard>
            )
          })}
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-3">
        {/* Recent Activity Feed */}
        <section className="xl:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-indigo-400" />
              <h3 className="font-semibold text-white">Recent Analyses</h3>
            </div>
            <button
              onClick={() => onNavigate?.('history')}
              className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
            >
              View all history <ChevronRight className="h-3 w-3" />
            </button>
          </div>

          <GradientCard hover={false} delay={0.15}>
            {history.length === 0 ? (
              <p className="py-8 text-center text-sm text-white/40">No database analyses recorded yet. Perform your first scan.</p>
            ) : (
              <div className="space-y-3">
                {history.map((item, i) => (
                  <motion.button
                    key={item.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    onClick={() => onOpenHistory?.(item.id)}
                    className="flex w-full items-center gap-3 rounded-xl border border-transparent px-3 py-3 text-left transition-all hover:border-white/10 hover:bg-white/[0.04]"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/5">
                      {item.analysis_type === 'youtube' ? (
                        <Youtube className="h-4 w-4 text-red-400" />
                      ) : (
                        <FileText className="h-4 w-4 text-indigo-400" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-white/40 uppercase">{item.analysis_type}</span>
                        {item.confidence_score != null && (
                          <span className="text-xs text-indigo-300 font-medium">({item.confidence_score}% confidence)</span>
                        )}
                      </div>
                      <p className="truncate text-sm font-medium text-white/90 mt-0.5">
                        {item.video_title || item.input_preview || item.youtube_url}
                      </p>
                      <p className="text-xs text-white/40 mt-0.5">
                        {formatDate(item.created_at)} · {(item.word_count ?? item.transcript_length ?? 0).toLocaleString()} words
                      </p>
                    </div>
                    <ResultBadge result={item.result} />
                  </motion.button>
                ))}
              </div>
            )}
          </GradientCard>
        </section>

        {/* Live System Status */}
        <section>
          <div className="mb-4 flex items-center gap-2">
            <Server className="h-4 w-4 text-cyan-400" />
            <h3 className="font-semibold text-white">System Status</h3>
          </div>

          <GradientCard hover={false} delay={0.2}>
            <div className="space-y-4">
              {healthRows.map((row) => (
                <div key={row.label} className="flex items-center justify-between border-b border-white/[0.04] pb-3 last:border-0 last:pb-0">
                  <span className="text-sm text-white/60 font-medium">{row.label}</span>
                  <span className={`flex items-center gap-2 text-xs font-semibold ${row.ok ? 'text-emerald-400' : 'text-amber-400'}`}>
                    <span className={`h-2 w-2 rounded-full ${row.ok ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          </GradientCard>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Detection Distribution */}
        <section>
          <div className="mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-violet-400" />
            <h3 className="font-semibold text-white">Detection Distribution</h3>
          </div>

          <GradientCard hover={false} delay={0.25}>
            {resultChartData.length > 0 ? (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={resultChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {resultChartData.map((entry) => (
                        <Cell key={entry.name} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="space-y-5 py-4">
                <StatBar label="Credible Content" value={crediblePct} count={stats?.credible_results ?? 0} color="bg-emerald-500" />
                <StatBar label="Suspicious Content" value={suspiciousPct} count={stats?.suspicious_results ?? 0} color="bg-red-500" />
              </div>
            )}
          </GradientCard>
        </section>

        {/* Analysis Trend Chart */}
        <section>
          <div className="mb-4 flex items-center gap-2">
            <Activity className="h-4 w-4 text-indigo-400" />
            <h3 className="font-semibold text-white">Analysis Trend (7 Days)</h3>
          </div>

          <GradientCard hover={false} delay={0.3}>
            {trends?.daily?.length ? (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trends.daily}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="date" stroke="rgba(255,255,255,0.4)" fontSize={12} />
                    <YAxis stroke="rgba(255,255,255,0.4)" fontSize={12} allowDecimals={false} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} dot={{ fill: '#6366f1' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="py-12 text-center text-sm text-white/40">No trend data yet</p>
            )}
          </GradientCard>
        </section>
      </div>
    </motion.div>
  )
}

function StatBar({ label, value, count, color }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-sm">
        <span className="text-white/60">{label}</span>
        <span className="font-medium text-white">
          {count} <span className="text-white/40">({value}%)</span>
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  )
}
