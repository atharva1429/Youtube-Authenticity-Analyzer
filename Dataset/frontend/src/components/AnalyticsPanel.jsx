import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
} from 'recharts'
import {
  BarChart3,
  FileText,
  Youtube,
  ShieldCheck,
  ShieldAlert,
  Activity,
  TrendingUp,
  CalendarDays,
  Percent,
} from 'lucide-react'
import { api } from '../api/client'
import GradientCard from './ui/GradientCard'
import AnimatedCounter from './ui/AnimatedCounter'

const PIE_COLORS = ['#22c55e', '#ef4444', '#64748b']

const tooltipStyle = {
  backgroundColor: 'rgba(12,12,20,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '12px',
  color: '#fff',
}

export default function AnalyticsPanel({ refreshKey = 0 }) {
  const [stats, setStats] = useState(null)
  const [trends, setTrends] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [s, t] = await Promise.all([
        api.getStats().catch((err) => {
          console.error('Failed to load stats:', err)
          return null
        }),
        api.getAnalyticsTrends().catch((err) => {
          console.error('Failed to load trends:', err)
          return null
        }),
      ])
      setStats(s)
      setTrends(t)
    } catch {
      setStats(null)
      setTrends(null)
    } finally {
      setLoading(false)
    }
  }, [])


  useEffect(() => {
    loadData()
  }, [loadData, refreshKey])

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] py-16 text-center text-white/50">
        Unable to load analytics data.
      </div>
    )
  }

  const crediblePct = stats.total_analyses ? Math.round((stats.credible_results / stats.total_analyses) * 100) : 0
  const suspiciousPct = stats.total_analyses ? Math.round((stats.suspicious_results / stats.total_analyses) * 100) : 0

  const resultData = [
    { name: 'Credible', value: stats.credible_results, fill: PIE_COLORS[0] },
    { name: 'Suspicious', value: stats.suspicious_results, fill: PIE_COLORS[1] },
    { name: 'Errors', value: stats.error_results, fill: PIE_COLORS[2] },
  ].filter((d) => d.value > 0)

  const typeData = [
    { name: 'Text', count: stats.text_analyses },
    { name: 'YouTube', count: stats.youtube_analyses },
  ]

  const statCards = [
    { label: 'Total Analyses', value: stats.total_analyses, icon: Activity, color: 'text-indigo-400', isPct: false },
    { label: 'Credible Analyses', value: stats.credible_results, icon: ShieldCheck, color: 'text-emerald-400', isPct: false },
    { label: 'Suspicious Analyses', value: stats.suspicious_results, icon: ShieldAlert, color: 'text-red-400', isPct: false },
    { label: 'Text Analyses', value: stats.text_analyses, icon: FileText, color: 'text-cyan-400', isPct: false },
    { label: 'YouTube Analyses', value: stats.youtube_analyses, icon: Youtube, color: 'text-red-400', isPct: false },
    { label: 'Credible Ratio', value: crediblePct, icon: Percent, color: 'text-emerald-400', isPct: true },
    { label: 'Suspicious Ratio', value: suspiciousPct, icon: Percent, color: 'text-red-400', isPct: true },
    { label: "Today's Scans", value: stats.today_analyses ?? 0, icon: CalendarDays, color: 'text-violet-400', isPct: false },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div>
        <div className="mb-2 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-indigo-400" />
          <h2 className="text-2xl font-semibold text-white">Analytics & Metrics</h2>
        </div>
        <p className="text-sm text-white/50">
          Real-time detection statistics and historical analysis breakdown powered by SQLite database.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card, i) => {
          const Icon = card.icon
          return (
            <GradientCard key={card.label} delay={i * 0.04} hover={false}>
              <div className="flex items-center gap-3">
                <div className={`rounded-xl bg-white/5 p-2.5 ${card.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white flex items-baseline gap-0.5">
                    <AnimatedCounter value={card.value} />
                    {card.isPct && <span className="text-sm font-medium text-white/60">%</span>}
                  </p>
                  <p className="text-xs text-white/40">{card.label}</p>
                </div>
              </div>
            </GradientCard>
          )
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <GradientCard delay={0.2}>
          <div className="mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-indigo-400" />
            <h3 className="font-semibold text-white">Text vs YouTube Analyses</h3>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" stroke="rgba(255,255,255,0.4)" fontSize={12} />
                <YAxis stroke="rgba(255,255,255,0.4)" fontSize={12} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="count" fill="#6366f1" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GradientCard>

        <GradientCard delay={0.25}>
          <div className="mb-4 flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-red-400" />
            <h3 className="font-semibold text-white">Credible vs Suspicious Breakdown</h3>
          </div>
          <div className="h-64">
            {resultData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={resultData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {resultData.map((entry, index) => (
                      <Cell key={entry.name} fill={entry.fill || PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend wrapperStyle={{ color: 'rgba(255,255,255,0.6)', fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-white/40">
                No analysis data available yet
              </div>
            )}
          </div>
        </GradientCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <GradientCard delay={0.3}>
          <div className="mb-4 flex items-center gap-2">
            <Activity className="h-4 w-4 text-cyan-400" />
            <h3 className="font-semibold text-white">Daily Analysis Trend (7 Days)</h3>
          </div>
          <div className="h-64">
            {trends?.daily?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trends.daily}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="date" stroke="rgba(255,255,255,0.4)" fontSize={12} />
                  <YAxis stroke="rgba(255,255,255,0.4)" fontSize={12} allowDecimals={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Line type="monotone" dataKey="count" name="Total" stroke="#6366f1" strokeWidth={2} dot={{ fill: '#6366f1' }} />
                  <Line type="monotone" dataKey="credible" name="Credible" stroke="#22c55e" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="suspicious" name="Suspicious" stroke="#ef4444" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-white/40">
                No trend data available yet.
              </div>

            )}
          </div>
        </GradientCard>

        <GradientCard delay={0.35}>
          <div className="mb-4 flex items-center gap-2">
            <CalendarDays className="h-4 w-4 text-violet-400" />
            <h3 className="font-semibold text-white">Weekly Activity (Past 4 Weeks)</h3>
          </div>
          <div className="h-64">
            {trends?.weekly?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trends.weekly.slice(-7)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="date" stroke="rgba(255,255,255,0.4)" fontSize={10} angle={-30} textAnchor="end" height={50} />
                  <YAxis stroke="rgba(255,255,255,0.4)" fontSize={12} allowDecimals={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="count" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-white/40">
                No trend data available yet.
              </div>

            )}
          </div>
        </GradientCard>
      </div>
    </motion.div>
  )
}
