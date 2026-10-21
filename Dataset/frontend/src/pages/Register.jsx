import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, UserPlus, Loader2, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import AuroraBackground, { FloatingParticles } from '../components/ui/AuroraBackground'

const features = [
  'Analyze text and YouTube transcripts',
  'Rule-based credibility indicators',
  'Full analysis history & reports',
]

export default function Register() {
  const { user, loading, register } = useAuth()
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' })
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

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (form.password !== form.confirm) {
      setError('Passwords do not match')
      return
    }

    if (form.password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setSubmitting(true)
    try {
      await register({
        username: form.username,
        email: form.email,
        password: form.password,
      })
    } catch (err) {
      setError(err.data?.detail || err.message || 'Registration failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuroraBackground className="flex min-h-screen items-center justify-center px-4 py-12">
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
          <h1 className="text-3xl font-bold tracking-tight text-white">Create Account</h1>
          <p className="mt-2 text-sm text-white/50">
            Create your YouTube Authenticity Analyzer account
          </p>

        </div>

        <div className="mb-6 space-y-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
          {features.map((f) => (
            <div key={f} className="flex items-center gap-2 text-xs text-white/50">
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
              {f}
            </div>
          ))}
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
                name="username"
                value={form.username}
                onChange={handleChange}
                className="input-field"
                placeholder="Choose a username"
                required
                minLength={3}
                autoComplete="username"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">Email</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                className="input-field"
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">Password</label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                className="input-field"
                placeholder="Min. 6 characters"
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/70">Confirm Password</label>
              <input
                type="password"
                name="confirm"
                value={form.confirm}
                onChange={handleChange}
                className="input-field"
                placeholder="Repeat password"
                required
                autoComplete="new-password"
              />
            </div>
          </div>

          <button type="submit" disabled={submitting} className="btn-primary mt-6 w-full">
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating account...
              </>
            ) : (
              <>
                <UserPlus className="h-4 w-4" />
                Create Account
              </>
            )}
          </button>

          <p className="mt-6 text-center text-sm text-white/40">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-indigo-400 transition-colors hover:text-white">
              Sign in
            </Link>
          </p>
        </form>
      </motion.div>
    </AuroraBackground>
  )
}
