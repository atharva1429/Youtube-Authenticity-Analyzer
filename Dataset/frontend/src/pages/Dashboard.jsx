import { useState } from 'react'
import { motion } from 'framer-motion'
import { Menu, X } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import TextAnalysis from '../components/TextAnalysis'
import YouTubeAnalysis from '../components/YouTubeAnalysis'
import HistoryPanel from '../components/HistoryPanel'
import OverviewDashboard from '../components/OverviewDashboard'
import AnalyticsPanel from '../components/AnalyticsPanel'
import HistoryDetailModal from '../components/HistoryDetailModal'
import AuroraBackground, { FloatingParticles } from '../components/ui/AuroraBackground'

const tabMeta = {
  overview: { title: 'Overview', subtitle: 'Dashboard & system insights' },
  text: { title: 'Text Analysis', subtitle: 'Analyze written content for authenticity' },
  youtube: { title: 'YouTube Analysis', subtitle: 'Scan video transcripts for credibility' },
  history: { title: 'History', subtitle: 'Browse and filter past analyses' },
  analytics: { title: 'Analytics', subtitle: 'Detection statistics and trends' },
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const [historyModalId, setHistoryModalId] = useState(null)

  const handleAnalysisComplete = () => {
    setRefreshKey((k) => k + 1)
  }

  const meta = tabMeta[activeTab] || tabMeta.overview

  return (
    <AuroraBackground>
      <FloatingParticles />

      <div className="relative flex min-h-screen w-full">
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <aside
          className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <Sidebar
            activeTab={activeTab}
            onTabChange={(tab) => {
              setActiveTab(tab)
              setSidebarOpen(false)
            }}
          />
        </aside>

        <main className="flex min-h-screen w-full min-w-0 flex-1 flex-col lg:pl-64">
          <header className="sticky top-0 z-30 flex items-center justify-between border-b border-white/[0.06] bg-[#050508]/80 px-4 py-4 backdrop-blur-xl lg:px-8">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen((open) => !open)}
                className="rounded-lg p-2 text-white/60 hover:bg-white/10 lg:hidden"
              >
                {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <div>
                <h1 className="text-lg font-semibold text-white">{meta.title}</h1>
                <p className="text-xs text-white/40">{meta.subtitle}</p>
              </div>
            </div>

            <div className="hidden items-center gap-2 md:flex">
              <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-3 py-1.5">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
                <span className="text-xs font-medium text-emerald-400">System Online</span>
              </div>
            </div>
          </header>

          <div className="flex-1 p-4 lg:p-8">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={activeTab === 'overview' || activeTab === 'analytics' ? 'mx-auto max-w-6xl' : 'mx-auto max-w-3xl'}
            >
              {activeTab === 'overview' && (
                <OverviewDashboard
                  refreshKey={refreshKey}
                  onNavigate={setActiveTab}
                  onOpenHistory={setHistoryModalId}
                />
              )}
              {activeTab === 'text' && (
                <TextAnalysis onAnalysisComplete={handleAnalysisComplete} />
              )}
              {activeTab === 'youtube' && (
                <YouTubeAnalysis onAnalysisComplete={handleAnalysisComplete} />
              )}
              {activeTab === 'history' && (
                <HistoryPanel
                  refreshKey={refreshKey}
                  onSelectItem={setHistoryModalId}
                />
              )}
              {activeTab === 'analytics' && (
                <AnalyticsPanel refreshKey={refreshKey} />
              )}
            </motion.div>
          </div>
        </main>
      </div>

      <HistoryDetailModal itemId={historyModalId} onClose={() => setHistoryModalId(null)} />
    </AuroraBackground>
  )
}
