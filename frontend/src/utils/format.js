export const fmtRace       = (t) => t != null ? t.toFixed(2) : '–'
export const fmtTrain      = (t) => t != null ? t.toFixed(3) : '–'
export const fmtPenalty    = (t) => t.toFixed(1)
export const fmtDelta      = (t, r) => `+${(t - r).toFixed(2)}`
export const fmtDeltaTrain = (t, r) => `+${(t - r).toFixed(3)}`

export function fmtDownhill(secs) {
  if (secs == null) return '–'
  const m = Math.floor(secs / 60)
  const s = (secs % 60).toFixed(2).padStart(5, '0')
  return m > 0 ? `${m}:${s}` : secs.toFixed(2)
}
