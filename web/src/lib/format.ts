export const seconds = (ms: number | null | undefined) =>
  typeof ms === 'number' && Number.isFinite(ms) ? (ms / 1000).toFixed(2) + ' s' : 'Unavailable'

export function bytes(value: number | null | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let index = 0
  while (value >= 1000 && index < units.length - 1) { value /= 1000; index++ }
  return (index && value < 100 ? value.toFixed(1) : Math.round(value)) + ' ' + units[index]
}

export const percent = (value: number, digits = 0) => (100 * value).toFixed(digits) + '%'

export const words = (key: string) => key.replaceAll('_', ' ')

/** Semantic tone for a 0–10 judge score. */
export const scoreTone = (score: number) => (score >= 7.5 ? 'good' : score >= 5 ? 'warn' : 'bad')

const relative = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })

export function ago(iso: string) {
  const diff = (new Date(iso).getTime() - Date.now()) / 1000
  if (!Number.isFinite(diff)) return ''
  const steps: [number, Intl.RelativeTimeFormatUnit][] = [[60, 'second'], [60, 'minute'], [24, 'hour'], [7, 'day'], [4.35, 'week'], [12, 'month'], [Infinity, 'year']]
  let value = diff
  for (const [size, unit] of steps) {
    if (Math.abs(value) < size) return relative.format(Math.round(value), unit)
    value /= size
  }
  return ''
}

export function dayLabel(iso: string) {
  const date = new Date(iso), today = new Date()
  const start = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const days = Math.round((start(today) - start(date)) / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  return date.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: date.getFullYear() === today.getFullYear() ? undefined : 'numeric' })
}

export const clock = (iso: string) => new Date(iso).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
