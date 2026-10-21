import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, LogIn, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import AuroraBackground, { FloatingParticles } from '../components/ui/AuroraBackground'

export default function Login() {
  const { user, loading, login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (loading) {
    return (
      <AuroraBackground className="flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </AuroraBackground>
    )
  }

  if (user) return <Navigate to="/dashboard" replace />

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login({ username, password })
    } catch (err) {
      setError(err.data?.detail || err.message || 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuroraBackground className="flex min-h-screen items-center justify-center px-4">
      <FloatingParticles />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="mb-8 text-center">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/20 shadow-[0_0_40px_rgba(99,102,241,0.2)]"
          >
            <Shield className="h-7 w-7 text-indigo-400" />
          </motion.div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Sign In</h1>
          <p className="mt-2 text-sm text-white/50">
            Access your YouTube Authenticity Analyzer account
          </p>

        </div>

        <form onSubmit={handleSubmit} className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 shadow-2xl backdrop-blur-xl">
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
            >
              {error}
            </motion.div>
          )}

          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field"
                placeholder="Enter your username"
                required
                autoComplete="username"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="Enter your password"
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          <button type="submit" disabled={submitting} className="btn-primary mt-6 w-full">
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" />
                Sign In
              </>
            )}
          </button>

          <p className="mt-6 text-center text-sm text-white/40">
            New here?{' '}
            <Link to="/register" className="font-medium text-indigo-400 transition-colors hover:text-white">
              Create your account
            </Link>
          </p>
        </form>
      </motion.div>
    </AuroraBackground>
  )
}
