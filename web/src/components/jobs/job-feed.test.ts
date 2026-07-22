import { describe, expect, it } from 'vitest'
import type { JobEvent, JobRow } from '../../api/services/jobs-service'
import {
  appendPage,
  applyJobEvent,
  applySnapshot,
  formatDurationMs,
  formatShortRelative,
  jobParamsText,
  matchesFilters,
  runningElapsedMs,
} from './job-feed'

function row(id: number, overrides: Partial<JobRow> = {}): JobRow {
  return {
    id,
    kind: 'generate_lecture_slide',
    status: 'queued',
    attempts: 1,
    max_attempts: 2,
    ...overrides,
  }
}

function event(id: number, overrides: Partial<JobEvent> = {}): JobEvent {
  return { id, kind: 'generate_lecture_slide', status: 'running', ...overrides }
}

describe('applyJobEvent', () => {
  it('patches a known job in place without refetching', () => {
    const jobs = [row(1), row(2)]
    const { jobs: next, needsHydration } = applyJobEvent(jobs, event(2), {})
    expect(needsHydration).toBeNull()
    expect(next[1].status).toBe('running')
    expect(next[0]).toBe(jobs[0]) // untouched rows keep identity
  })

  it('keeps a card whose new status no longer matches the status filter', () => {
    const jobs = [row(1, { status: 'running' })]
    const { jobs: next } = applyJobEvent(jobs, event(1, { status: 'done' }), {
      status: 'running',
    })
    expect(next).toHaveLength(1)
    expect(next[0].status).toBe('done')
  })

  it('extracts duration telemetry from a terminal event result', () => {
    const jobs = [row(1, { status: 'running' })]
    const { jobs: next } = applyJobEvent(
      jobs,
      event(1, { status: 'done', result: { _job_telemetry: { duration_ms: 63000 } } }),
      {}
    )
    expect(next[0].duration_ms).toBe(63000)
  })

  it('prepends an unknown matching job and requests hydration', () => {
    const jobs = [row(1)]
    const { jobs: next, needsHydration } = applyJobEvent(jobs, event(99), {})
    expect(needsHydration).toBe(99)
    expect(next[0].id).toBe(99)
    expect(next).toHaveLength(2)
  })

  it('ignores an unknown job that does not match the filters', () => {
    const jobs = [row(1)]
    const kindMismatch = applyJobEvent(jobs, event(99), { kind: 'generate_lecture_audio' })
    expect(kindMismatch.jobs).toBe(jobs)
    expect(kindMismatch.needsHydration).toBeNull()

    const statusMismatch = applyJobEvent(jobs, event(99, { status: 'running' }), {
      status: 'failed',
    })
    expect(statusMismatch.jobs).toBe(jobs)
  })

  it('caps the feed length', () => {
    const jobs = [row(1), row(2), row(3)]
    const { jobs: next } = applyJobEvent(jobs, event(99), {}, 3)
    expect(next).toHaveLength(3)
    expect(next[0].id).toBe(99)
    expect(next[2].id).toBe(2)
  })
})

describe('applySnapshot', () => {
  it('patches known jobs and prepends unknown matching rows, newest first', () => {
    const jobs = [row(5), row(3)]
    const snapshot = [row(3, { status: 'running' }), row(8), row(10)]
    const next = applySnapshot(jobs, snapshot, {})
    expect(next.map((job) => job.id)).toEqual([10, 8, 5, 3])
    expect(next.find((job) => job.id === 3)?.status).toBe('running')
  })

  it('never clears the list and respects filters for new rows', () => {
    const jobs = [row(5)]
    const next = applySnapshot(jobs, [row(8, { kind: 'generate_lecture_audio' })], {
      kind: 'generate_lecture_slide',
    })
    expect(next.map((job) => job.id)).toEqual([5])
  })
})

describe('appendPage', () => {
  it('appends older rows and drops duplicates already in the feed', () => {
    const jobs = [row(10), row(9)]
    const next = appendPage(jobs, [row(9), row(8)])
    expect(next.map((job) => job.id)).toEqual([10, 9, 8])
  })
})

describe('matchesFilters', () => {
  it('matches on both status and kind when set', () => {
    expect(matchesFilters(row(1), {})).toBe(true)
    expect(matchesFilters(row(1), { status: 'queued' })).toBe(true)
    expect(matchesFilters(row(1), { status: 'done' })).toBe(false)
    expect(matchesFilters(row(1), { kind: 'generate_lecture_slide' })).toBe(true)
    expect(matchesFilters(row(1), { kind: 'other' })).toBe(false)
  })
})

describe('jobParamsText', () => {
  it('reads ids from payload and partial_attributes', () => {
    expect(jobParamsText(row(1, { payload: { lecture_id: 482, topic_id: 1778 } }))).toBe(
      'lecture 482 · topic 1778'
    )
    expect(jobParamsText(row(1, { payload: { partial_attributes: { course_id: 7 } } }))).toBe(
      'course 7'
    )
    expect(jobParamsText(row(1))).toBe('')
  })
})

describe('formatting helpers', () => {
  it('formats short relative times', () => {
    const now = Date.parse('2026-07-22T12:00:00Z')
    expect(formatShortRelative('2026-07-22T11:59:30Z', now)).toBe('30s')
    expect(formatShortRelative('2026-07-22T11:30:00Z', now)).toBe('30m')
    expect(formatShortRelative('2026-07-21T12:00:00Z', now)).toBe('24h')
    expect(formatShortRelative(undefined, now)).toBe('-')
  })

  it('formats durations', () => {
    expect(formatDurationMs(63000)).toBe('63s')
    expect(formatDurationMs(185000)).toBe('3m 05s')
    expect(formatDurationMs(null)).toBe('-')
  })

  it('computes plausible running elapsed time only', () => {
    const now = Date.parse('2026-07-22T12:00:00Z')
    const running = row(1, { status: 'running', updated_at: '2026-07-22T11:59:00Z' })
    expect(runningElapsedMs(running, now)).toBe(60000)
    const stale = row(1, { status: 'running', updated_at: '2026-07-19T11:59:00Z' })
    expect(runningElapsedMs(stale, now)).toBeNull()
    expect(runningElapsedMs(row(1, { status: 'running' }), now)).toBeNull()
  })
})
