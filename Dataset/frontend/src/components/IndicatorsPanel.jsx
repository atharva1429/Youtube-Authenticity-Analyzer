import { motion } from 'framer-motion'
import { AlertTriangle, ShieldAlert } from 'lucide-react'

export default function IndicatorsPanel({ indicators = [], compact = false }) {
  if (!indicators?.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={compact ? 'mt-4' : 'mt-6'}
    >
      <div className="mb-3 flex items-center gap-2">
        <ShieldAlert className="h-4 w-4 text-amber-400" />
        <h4 className="text-sm font-semibold text-white">Indicators Detected</h4>
      </div>
      <div className={`grid gap-2 ${compact ? 'grid-cols-1' : 'sm:grid-cols-2'}`}>
        {indicators.map((indicator, index) => (
          <motion.div
            key={indicator}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-start gap-2 rounded-xl border border-amber-500/20 bg-amber-500/5 px-3 py-2.5"
          >
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />
            <span className="text-sm text-amber-100/90">{indicator}</span>
          </motion.div>
        ))}
      </div>
      <p className="mt-3 text-xs text-white/40">
        Rule-based signals derived from text patterns — not probability scores.
      </p>
    </motion.div>
  )
}
