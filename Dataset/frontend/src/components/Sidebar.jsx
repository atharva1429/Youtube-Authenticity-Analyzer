import { motion } from 'framer-motion'
import {
  Shield,
  FileText,
  Youtube,
  History,
  LogOut,
  Sparkles,
  LayoutDashboard,
  BarChart3,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'text', label: 'Text Analysis', icon: FileText },
  { id: 'youtube', label: 'YouTube Analysis', icon: Youtube },
  { id: 'history', label: 'History', icon: History },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
]

export default function Sidebar({ activeTab, onTabChange }) {
  const { user, logout } = useAuth()

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="flex h-full w-full flex-col border-r border-white/[0.06] bg-[#09090f]/95 backdrop-blur-2xl"
    >
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-6 py-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/30 to-violet-500/20 shadow-lg">
          <Shield className="h-5 w-5 text-indigo-300" />
        </div>
        <div className="min-w-0">
          <h1 className="truncate text-sm font-bold text-white">YouTube Authenticity</h1>
          <p className="text-xs font-medium text-indigo-400">Analyzer</p>
        </div>
      </div>


      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = activeTab === item.id
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`group flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 ${
                active
                  ? 'bg-indigo-500/20 text-white shadow-[0_0_20px_rgba(99,102,241,0.15)]'
                  : 'text-white/50 hover:bg-white/5 hover:text-white/80'
              }`}
            >
              <Icon className={`h-4 w-4 ${active ? 'text-indigo-400' : 'text-white/40 group-hover:text-white/60'}`} />
              {item.label}
            </button>
          )
        })}
      </nav>

      <div className="border-t border-white/[0.06] p-4">
        <div className="mb-3 rounded-xl border border-white/[0.06] bg-white/[0.03] px-4 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span className="text-xs text-white/40">Signed in as</span>
          </div>
          <p className="mt-1 truncate text-sm font-medium text-white">{user?.username}</p>
        </div>
        <button
          onClick={logout}
          className="btn-ghost w-full text-red-400 hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-300"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </motion.aside>
  )
}
