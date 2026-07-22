/**
 * Pure helpers for the admin jobs dashboard feed.
 *
 * The feed is updated in place from SSE events — never by refetching the whole
 * list — so these functions take the current array and return a new one.
 */

import type { JobEvent, JobRow } from '../../api/services/jobs-service'

export interface JobFeedFilters {
  status?: JobRow['status']
  kind?: string
}

export const FEED_CAP = 200

export function durationMsFromResult(result: unknown): number | null {
  if (!result || typeof result !== 'object') return null
  const o = result as { _job_telemetry?: { duration_ms?: number } }
  const ms = o._job_telemetry?.duration_ms
  return typeof ms === 'number' && !Number.isNaN(ms) ? ms : null
}

export function matchesFilters(
  job: Pick<JobRow, 'kind' | 'status'>,
  filters: JobFeedFilters
): boolean {
  if (filters.status && job.status !== filters.status) return false
  if (filters.kind && job.kind !== filters.kind) return false
  return true
}

/** Minimal placeholder row for a job first seen via SSE; hydrated by a getJob fetch. */
export function provisionalRowFromEvent(event: JobEvent): JobRow {
  const nowIso = new Date().toISOString()
  return {
    id: event.id,
    kind: event.kind,
    status: event.status,
    attempts: 1,
    max_attempts: 1,
    payload: event.payload,
    result: event.result,
    last_error: event.last_error ?? null,
    duration_ms: durationMsFromResult(event.result),
    created_at: nowIso,
    updated_at: nowIso,
  }
}

function patchedRow(row: JobRow, event: JobEvent): JobRow {
  const eventDuration = event.result !== undefined ? durationMsFromResult(event.result) : null
  return {
    ...row,
    status: event.status,
    last_error: event.last_error || row.last_error,
    result: event.result !== undefined ? event.result : row.result,
    duration_ms: eventDuration ?? row.duration_ms,
    updated_at: new Date().toISOString(),
  }
}

export interface ApplyJobEventResult {
  jobs: JobRow[]
  /** Job id to fetch fully (a job first seen via SSE), or null. */
  needsHydration: number | null
}

/**
 * Fold one SSE event into the feed.
 *
 * Known jobs are patched in place and deliberately kept even when their new
 * status no longer matches the active filter — watching a card transition
 * queued -> running -> done is the point of the page. Unknown jobs are
 * prepended (as provisional rows) only when they match the filters.
 */
export function applyJobEvent(
  jobs: JobRow[],
  event: JobEvent,
  filters: JobFeedFilters,
  cap: number = FEED_CAP
): ApplyJobEventResult {
  const index = jobs.findIndex((job) => job.id === event.id)
  if (index !== -1) {
    const next = [...jobs]
    next[index] = patchedRow(jobs[index], event)
    return { jobs: next, needsHydration: null }
  }

  if (!matchesFilters(event, filters)) {
    return { jobs, needsHydration: null }
  }

  const next = [provisionalRowFromEvent(event), ...jobs].slice(0, cap)
  return { jobs: next, needsHydration: event.id }
}

/**
 * Fold an SSE snapshot (full server rows for active jobs) into the feed.
 * Patches known jobs and prepends unknown matching ones; never clears the list.
 */
export function applySnapshot(
  jobs: JobRow[],
  snapshot: Array<JobEvent | JobRow>,
  filters: JobFeedFilters,
  cap: number = FEED_CAP
): JobRow[] {
  let next = [...jobs]
  const toPrepend: JobRow[] = []

  for (const item of snapshot) {
    const index = next.findIndex((job) => job.id === item.id)
    if (index !== -1) {
      next[index] = { ...next[index], ...item }
      continue
    }
    if (!matchesFilters(item, filters)) continue
    const full = 'attempts' in item ? item : provisionalRowFromEvent(item)
    toPrepend.push(full)
  }

  if (toPrepend.length > 0) {
    // Newest first, consistent with the feed ordering.
    toPrepend.sort((a, b) => b.id - a.id)
    next = [...toPrepend, ...next]
  }
  return next.slice(0, cap)
}

/** Append an older page from the API, dropping any rows already in the feed. */
export function appendPage(jobs: JobRow[], page: JobRow[]): JobRow[] {
  const known = new Set(jobs.map((job) => job.id))
  return [...jobs, ...page.filter((job) => !known.has(job.id))]
}

/** Entity references from a job payload, e.g. "lecture 482 · topic 1778". */
export function jobParamsText(job: JobRow): string {
  const payload = (job.payload ?? {}) as Record<string, unknown>
  const partial = (payload.partial_attributes ?? {}) as Record<string, unknown>

  const pick = (key: string): string | null => {
    for (const source of [payload, partial]) {
      const value = source[key]
      if (typeof value === 'string' || typeof value === 'number') return String(value)
    }
    return null
  }

  const parts: string[] = []
  const lectureId = pick('lecture_id')
  if (lectureId) parts.push(`lecture ${lectureId}`)
  const topicId = pick('topic_id')
  if (topicId) parts.push(`topic ${topicId}`)
  const courseId = pick('course_id')
  if (courseId) parts.push(`course ${courseId}`)
  return parts.join(' · ')
}

/** Compact relative time: "12s", "3m", "2h", "5d". */
export function formatShortRelative(iso: string | undefined, nowMs: number): string {
  if (!iso) return '-'
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return '-'
  const sec = Math.max(0, Math.round((nowMs - then) / 1000))
  if (sec < 60) return `${String(sec)}s`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${String(min)}m`
  const hours = Math.floor(min / 60)
  if (hours < 48) return `${String(hours)}h`
  return `${String(Math.floor(hours / 24))}d`
}

/** Duration in whole seconds ("63s") or minutes+seconds ("2m 05s"). */
export function formatDurationMs(ms: number | null | undefined): string {
  if (ms == null || Number.isNaN(ms)) return '-'
  const sec = Math.round(ms / 1000)
  if (sec < 120) return `${String(sec)}s`
  const min = Math.floor(sec / 60)
  const rest = sec % 60
  return `${String(min)}m ${String(rest).padStart(2, '0')}s`
}

/**
 * Live elapsed time for a running job, from its last transition to running.
 * Returns null when the timestamp is missing or implausible (e.g. clock skew).
 */
export function runningElapsedMs(job: JobRow, nowMs: number): number | null {
  const since = job.updated_at ?? job.created_at
  if (!since) return null
  const then = new Date(since).getTime()
  if (Number.isNaN(then)) return null
  const elapsed = nowMs - then
  if (elapsed < 0 || elapsed > 24 * 60 * 60 * 1000) return null
  return elapsed
}
