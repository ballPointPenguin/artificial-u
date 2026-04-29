/**
 * Format a date to a localized string
 */
export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

/**
 * Get a relative time string (e.g., "2 days ago")
 */
export function getRelativeTimeString(date: Date): string {
  const now = new Date()
  const diffInMs = now.getTime() - date.getTime()
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

  if (diffInDays === 0) return 'Today'
  if (diffInDays === 1) return 'Yesterday'
  if (diffInDays < 7) return `${String(diffInDays)} days ago`

  return formatDate(date)
}

/**
 * Format a date to simple format without time (e.g., "Sep. 12, 2025")
 */
export function formatDateSimple(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return dateObj.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Format a date as a local ISO-like timestamp without timezone.
 * Example: "2026-04-28T17:42:09"
 */
export function formatLocalDateTimeISO(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  if (Number.isNaN(dateObj.getTime())) return '-'

  const pad = (value: number) => String(value).padStart(2, '0')

  return [
    `${String(dateObj.getFullYear())}-${pad(dateObj.getMonth() + 1)}-${pad(dateObj.getDate())}`,
    `${pad(dateObj.getHours())}:${pad(dateObj.getMinutes())}:${pad(dateObj.getSeconds())}`,
  ].join('T')
}
