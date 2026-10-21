import { motion } from 'framer-motion'

export default function GradientCard({ children, className = '', delay = 0, hover = true }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={hover ? { y: -4, transition: { duration: 0.2 } } : undefined}
      className={`group relative overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 backdrop-blur-xl ${className}`}
    >
      <div className="pointer-events-none absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500/10 via-transparent to-violet-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-br from-indigo-500/20 via-transparent to-violet-500/10 opacity-0 transition-opacity duration-300 group-hover:opacity-100" style={{ mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)', maskComposite: 'exclude', padding: '1px' }} />
      <div className="relative">{children}</div>
    </motion.div>
  )
}
