export function formatDate(dateStr) {
  if (!dateStr) return '—'
  let dateObj = new Date(dateStr)
  if (typeof dateStr === 'string' && !dateStr.endsWith('Z') && !dateStr.includes('+')) {
    dateObj = new Date(dateStr + 'Z')
  }
  return dateObj.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}


export const REPORT_REASONS = [
  'Fake News',
  'Misinformation',
  'Manipulated Content',
  'Clickbait',
  'Hate Speech',
  'Other',
]

export function strengthColor(strength) {
  if (strength === 'High') return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30'
  if (strength === 'Medium') return 'text-amber-400 bg-amber-400/10 border-amber-400/30'
  return 'text-slate-400 bg-slate-400/10 border-slate-400/30'
}
