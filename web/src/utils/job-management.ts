/**
 * Centralized job management utilities for tracking background jobs
 * and their states across components.
 */

import { type Accessor, createEffect, createMemo, createSignal, on, onCleanup } from 'solid-js'
import { TIMEOUT_CONFIG } from '../api/config.js'
import {
  getJob,
  type JobEvent,
  type JobRow,
  type JobStatus,
  listJobChildren,
  listJobs,
} from '../api/services/jobs-service.js'
import { jobDebug } from './job-debug.js'

const DEFAULT_JOB_POLL_INTERVAL_MS = 2000
const TERMINAL_JOB_STATUSES = new Set<JobStatus>(['done', 'failed', 'cancelled'])
const ACTIVE_JOB_STATUSES = new Set<JobStatus>(['queued', 'running'])
const DEFAULT_JOB_HANDOFF_TTL_MS = 10 * 60_000

export interface JobTrackerOptions {
  topicId?: () => number | undefined
  lectureId?: () => number | undefined
  courseId?: () => number | undefined
  kinds?: string[]
  pollIntervalMs?: number
  /** When true, automatically track child jobs when a parent job completes. */
  trackChildren?: boolean
  onJobComplete?: (event: JobEvent) => void
  onJobStart?: (event: JobEvent) => void
  onJobFail?: (event: JobEvent) => void
}

export interface JobHandoffEntity {
  type: 'course'
  id: number
}

export interface JobHandoff {
  entity: JobHandoffEntity
  parentJobIds?: number[]
  jobIds?: number[]
  kinds?: string[]
  expiresAt?: number
}

export interface JobHandoffAdoptionOptions {
  entity: MaybeAccessor<JobHandoffEntity | null | undefined>
  kinds?: string[]
  pollIntervalMs?: number
  fallback?: MaybeAccessor<boolean>
  onJobComplete?: (event: JobEvent) => void
  onJobStart?: (event: JobEvent) => void
  onJobFail?: (event: JobEvent) => void
}

const jobHandoffs = new Map<string, Required<JobHandoff>>()
const fallbackAttemptKeys = new Set<string>()

function uniqueNumbers(values: Array<number | null | undefined>): number[] {
  return [...new Set(values.filter((value): value is number => typeof value === 'number'))]
}

function handoffKey(entity: JobHandoffEntity): string {
  return `${entity.type}:${String(entity.id)}`
}

function normalizeJobHandoff(handoff: JobHandoff): Required<JobHandoff> {
  return {
    entity: handoff.entity,
    parentJobIds: uniqueNumbers(handoff.parentJobIds ?? []),
    jobIds: uniqueNumbers(handoff.jobIds ?? []),
    kinds: [...new Set(handoff.kinds ?? [])],
    expiresAt: handoff.expiresAt ?? Date.now() + DEFAULT_JOB_HANDOFF_TTL_MS,
  }
}

function pruneJobHandoffs(now = Date.now()) {
  for (const [key, handoff] of jobHandoffs.entries()) {
    if (handoff.expiresAt <= now) {
      jobHandoffs.delete(key)
      fallbackAttemptKeys.delete(key)
    }
  }
}

export function registerJobHandoff(handoff: JobHandoff) {
  pruneJobHandoffs()
  const key = handoffKey(handoff.entity)
  const existing = jobHandoffs.get(key)
  const next = normalizeJobHandoff(handoff)

  if (!existing) {
    jobHandoffs.set(key, next)
    return
  }

  jobHandoffs.set(key, {
    entity: next.entity,
    parentJobIds: uniqueNumbers([...existing.parentJobIds, ...next.parentJobIds]),
    jobIds: uniqueNumbers([...existing.jobIds, ...next.jobIds]),
    kinds: [...new Set([...existing.kinds, ...next.kinds])],
    expiresAt: Math.max(existing.expiresAt, next.expiresAt),
  })
}

function toJobEvent(job: JobRow): JobEvent {
  return {
    id: job.id,
    kind: job.kind,
    status: job.status,
    payload: job.payload,
    result: job.result,
    last_error: job.last_error ?? undefined,
  }
}

function matchesJobKind(job: JobRow, kinds?: string[]): boolean {
  return !kinds || kinds.includes(job.kind)
}

/**
 * Creates a reactive job tracker for jobs started by this page instance.
 *
 * Call `track(job.id)` after enqueueing a job. The tracker polls only those
 * known job IDs and stops when each reaches a terminal state.
 */
export function createJobTracker(options: JobTrackerOptions) {
  const [activeJobIds, setActiveJobIds] = createSignal<Set<number>>(new Set())
  const [isInitializing] = createSignal(false)
  const [lastError, setLastError] = createSignal<string | null>(null)

  let pollTimers = new Map<number, ReturnType<typeof setTimeout>>()
  let startedJobIds = new Set<number>()
  let runId = 0

  // Computed signal for whether any jobs are active
  const hasActiveJobs = () => activeJobIds().size > 0

  // Debug logging
  jobDebug.log('subscription', 'JobTracker initializing', {
    topicId: options.topicId?.(),
    lectureId: options.lectureId?.(),
    courseId: options.courseId?.(),
    kinds: options.kinds,
  })

  const clearPollTimer = (jobId: number) => {
    const timer = pollTimers.get(jobId)
    if (timer) {
      clearTimeout(timer)
      pollTimers.delete(jobId)
    }
  }

  const clearAllPollTimers = () => {
    for (const timer of pollTimers.values()) {
      clearTimeout(timer)
    }
    pollTimers = new Map<number, ReturnType<typeof setTimeout>>()
  }

  const removeActiveJob = (jobId: number) => {
    setActiveJobIds((prev) => {
      const next = new Set(prev)
      next.delete(jobId)
      return next
    })
  }

  const stop = (jobId?: number) => {
    if (jobId === undefined) {
      console.log(
        `[job-chain] stop() ALL called, runId ${String(runId)} → ${String(runId + 1)}, activeIds=${JSON.stringify([...activeJobIds()])}`
      )
      runId += 1
      clearAllPollTimers()
      setActiveJobIds(new Set<number>())
      startedJobIds = new Set<number>()
      return
    }

    clearPollTimer(jobId)
    removeActiveJob(jobId)
    startedJobIds.delete(jobId)
  }

  const markActiveJob = (jobId: number) => {
    setActiveJobIds((prev) => {
      if (prev.has(jobId)) return prev
      const next = new Set(prev)
      next.add(jobId)
      return next
    })
  }

  const scheduleNextPoll = (jobId: number, poll: () => void) => {
    clearPollTimer(jobId)
    pollTimers.set(jobId, setTimeout(poll, options.pollIntervalMs ?? DEFAULT_JOB_POLL_INTERVAL_MS))
  }

  const trackJobChildren = (job: JobRow) => {
    void (async () => {
      try {
        console.log(
          `[job-chain] trackJobChildren: job=${job.kind}#${String(job.id)} parent_job_id=${String(job.parent_job_id)} runId=${String(runId)}`
        )

        // Direct children of the completing job
        const children = await listJobChildren(job.id)
        console.log(
          `[job-chain] children of #${String(job.id)}:`,
          children.map((c) => `${c.kind}#${String(c.id)}(${c.status})`)
        )
        for (const child of children) {
          if (!TERMINAL_JOB_STATUSES.has(child.status)) {
            jobDebug.log(
              'state_change',
              `Auto-tracking child job ${child.kind} #${String(child.id)}`,
              { parentId: job.id }
            )
            console.log(
              `[job-chain] tracking child #${String(child.id)} (${child.kind}) runId=${String(runId)}`
            )
            track(child.id)
          }
        }

        // Siblings: if this job has a parent, also check parent's children.
        // Handles sequential chains (e.g. lecture slides) where each slide's
        // successor is a sibling (same parent_job_id), not a child.
        if (job.parent_job_id != null) {
          const siblings = await listJobChildren(job.parent_job_id)
          console.log(
            `[job-chain] siblings of parent#${String(job.parent_job_id)}:`,
            siblings.map((s) => `${s.kind}#${String(s.id)}(${s.status})`)
          )
          for (const sibling of siblings) {
            if (!TERMINAL_JOB_STATUSES.has(sibling.status) && sibling.id !== job.id) {
              jobDebug.log(
                'state_change',
                `Auto-tracking sibling job ${sibling.kind} #${String(sibling.id)}`,
                { parentId: job.parent_job_id }
              )
              console.log(
                `[job-chain] tracking sibling #${String(sibling.id)} (${sibling.kind}) runId=${String(runId)}`
              )
              track(sibling.id)
            }
          }
        }
      } catch (err) {
        console.warn('[job-chain] trackJobChildren error:', err)
        // Non-fatal: child tracking is best-effort
      }
    })()
  }

  const handlePolledJob = (job: JobRow) => {
    if (!matchesJobKind(job, options.kinds)) {
      console.log(
        `[job-chain] handlePolledJob: #${String(job.id)} (${job.kind}) FILTERED OUT by kinds`
      )
      removeActiveJob(job.id)
      return false
    }
    console.log(
      `[job-chain] handlePolledJob: #${String(job.id)} (${job.kind}) status=${job.status} activeIds=${JSON.stringify([...activeJobIds()])} runId=${String(runId)}`
    )

    if (isActiveJobStatus(job.status)) {
      markActiveJob(job.id)

      if (!startedJobIds.has(job.id)) {
        startedJobIds.add(job.id)
        jobDebug.log('state_change', `Job active: ${job.kind} #${String(job.id)}`, {
          id: job.id,
          kind: job.kind,
          status: job.status,
        })
        options.onJobStart?.(toJobEvent(job))
      }

      return true
    }

    removeActiveJob(job.id)
    clearPollTimer(job.id)
    startedJobIds.delete(job.id)

    if (job.status === 'done') {
      jobDebug.log('state_change', `Job completed: ${job.kind} #${String(job.id)}`, job)
      if (options.trackChildren) {
        trackJobChildren(job)
      }
      options.onJobComplete?.(toJobEvent(job))
    } else if (job.status === 'failed' || job.status === 'cancelled') {
      setLastError(`Job ${job.kind} failed`)
      options.onJobFail?.(toJobEvent(job))
    }

    return false
  }

  const track = (jobId: number) => {
    const currentRunId = runId
    console.log(`[job-chain] track called: #${String(jobId)} currentRunId=${String(currentRunId)}`)
    markActiveJob(jobId)
    setLastError(null)

    const poll = () => {
      void (async () => {
        if (currentRunId !== runId) {
          console.log(
            `[job-chain] poll aborted (stale runId): job#${String(jobId)} currentRunId=${String(currentRunId)} runId=${String(runId)}`
          )
          return
        }

        try {
          const job = await getJob(jobId)
          if (currentRunId !== runId) {
            console.log(
              `[job-chain] poll result discarded (stale runId after fetch): job#${String(jobId)}`
            )
            return
          }
          if (!activeJobIds().has(jobId)) {
            console.log(
              `[job-chain] poll result discarded (not in activeJobIds): job#${String(jobId)} activeIds=${JSON.stringify([...activeJobIds()])}`
            )
            return
          }

          const shouldContinue = handlePolledJob(job)
          if (shouldContinue) {
            scheduleNextPoll(jobId, poll)
          }
        } catch (error) {
          if (currentRunId !== runId) return
          jobDebug.log('error', `Failed to poll job ${String(jobId)}`, error)
          setLastError('Failed to load job status')
          scheduleNextPoll(jobId, poll)
        }
      })()
    }

    jobDebug.log('state_change', `Tracking job ${String(jobId)}`, null)
    poll()
  }

  // Stop only when navigating to a different entity (ID changed from one defined value to another).
  // Do NOT stop when an ID first becomes defined — that's new data arriving (e.g. lecture created),
  // not navigation, and killing the tracker here would drop child-job polling.
  createEffect(
    on(
      () => [options.topicId?.(), options.lectureId?.(), options.courseId?.()] as const,
      ([newTopicId, newLectureId, newCourseId], prev) => {
        const [prevTopicId, prevLectureId, prevCourseId] = prev ?? [undefined, undefined, undefined]
        const navigated = (p: number | undefined, n: number | undefined) =>
          p != null && n != null && p !== n
        if (
          navigated(prevTopicId, newTopicId) ||
          navigated(prevLectureId, newLectureId) ||
          navigated(prevCourseId, newCourseId)
        ) {
          console.log(
            `[job-chain] entity navigation detected (prev=[${String(prevTopicId)},${String(prevLectureId)},${String(prevCourseId)}] → next=[${String(newTopicId)},${String(newLectureId)},${String(newCourseId)}]), stopping tracker`
          )
          stop()
          setLastError(null)
        }
      },
      { defer: true }
    )
  )

  // Cleanup on unmount
  onCleanup(() => {
    jobDebug.log('subscription', 'Cleaning up job polling', null)
    stop()
  })

  return {
    track,
    stop,
    hasActiveJobs,
    activeJobIds,
    isInitializing,
    lastError,
    clearError: () => setLastError(null),
  }
}

export function adoptJobHandoff(options: JobHandoffAdoptionOptions) {
  const trackedJobIds = new Set<number>()

  const entity = () => resolveMaybeAccessor(options.entity)
  const fallbackEnabled = () =>
    options.fallback === undefined ? false : resolveMaybeAccessor(options.fallback)

  const tracker = createJobTracker({
    courseId: () => {
      const currentEntity = entity()
      return currentEntity?.type === 'course' ? currentEntity.id : undefined
    },
    kinds: options.kinds,
    pollIntervalMs: options.pollIntervalMs,
    trackChildren: true,
    onJobStart: options.onJobStart,
    onJobComplete: options.onJobComplete,
    onJobFail: options.onJobFail,
  })

  const trackOnce = (jobId: number | null | undefined) => {
    if (jobId == null || trackedJobIds.has(jobId)) return
    trackedJobIds.add(jobId)
    tracker.track(jobId)
  }

  const discoverChildren = async (parentJobIds: number[]) => {
    await Promise.all(
      parentJobIds.map(async (parentJobId) => {
        try {
          const children = await listJobChildren(parentJobId)
          for (const child of children) {
            if (matchesJobKind(child, options.kinds)) {
              trackOnce(child.id)
            }
          }
        } catch (error) {
          jobDebug.log('error', `Failed to adopt child jobs for ${String(parentJobId)}`, error)
        }
      })
    )
  }

  const adoptRegisteredHandoff = async (currentEntity: JobHandoffEntity): Promise<boolean> => {
    pruneJobHandoffs()
    const key = handoffKey(currentEntity)
    const handoff = jobHandoffs.get(key)
    if (!handoff) return false

    for (const jobId of handoff.parentJobIds) trackOnce(jobId)
    for (const jobId of handoff.jobIds) trackOnce(jobId)
    await discoverChildren(handoff.parentJobIds)
    return true
  }

  const discoverActiveCourseJobs = async (currentEntity: JobHandoffEntity) => {
    try {
      const [queued, running] = await Promise.all([
        listJobs({ course_id: currentEntity.id, status: 'queued', limit: 100 }),
        listJobs({ course_id: currentEntity.id, status: 'running', limit: 100 }),
      ])
      const activeJobs = [...queued, ...running].filter((job) => matchesJobKind(job, options.kinds))
      for (const job of activeJobs) trackOnce(job.id)
      await discoverChildren(activeJobs.map((job) => job.id))
    } catch (error) {
      jobDebug.log(
        'error',
        `Failed to discover active jobs for course ${String(currentEntity.id)}`,
        error
      )
    }
  }

  createEffect(
    on(
      () => [entity(), fallbackEnabled()] as const,
      ([currentEntity, shouldFallback]) => {
        if (!currentEntity) return
        const key = handoffKey(currentEntity)

        void (async () => {
          const adopted = await adoptRegisteredHandoff(currentEntity)
          if (adopted || !shouldFallback || fallbackAttemptKeys.has(key)) return

          fallbackAttemptKeys.add(key)
          await discoverActiveCourseJobs(currentEntity)
        })()
      },
      { defer: false }
    )
  )

  return tracker
}

/**
 * Helper to determine if a job affects a specific entity
 */
export function isJobForEntity(
  event: JobEvent | JobRow,
  entityType: 'lecture' | 'topic' | 'course',
  entityId: number
): boolean {
  const payload = 'payload' in event ? event.payload : {}

  if (!payload || typeof payload !== 'object') return false

  const p = payload as Record<string, unknown>

  switch (entityType) {
    case 'lecture':
      return p.lecture_id === entityId

    case 'topic':
      // Check both direct topic_id and nested in partial_attributes
      return (
        (p.topic_id as number | undefined) === entityId ||
        ((p.partial_attributes as Record<string, unknown> | undefined)?.topic_id as
          | number
          | undefined) === entityId
      )

    case 'course':
      return (
        (p.course_id as number | undefined) === entityId ||
        ((p.partial_attributes as Record<string, unknown> | undefined)?.course_id as
          | number
          | undefined) === entityId
      )

    default:
      return false
  }
}

/**
 * Get a user-friendly message for a job kind
 */
export function getJobMessage(
  kind: string,
  status: 'queued' | 'running' | 'done' | 'failed' | 'cancelled'
): string {
  const messages: Record<string, Record<string, string> | undefined> = {
    generate_lecture: {
      queued: 'Lecture generation queued...',
      running: 'Generating lecture content...',
      done: 'Lecture generated successfully!',
      failed: 'Lecture generation failed',
      cancelled: 'Lecture generation cancelled',
    },
    generate_lecture_text_only: {
      queued: 'Lecture text generation queued...',
      running: 'Generating lecture text...',
      done: 'Lecture text generated successfully!',
      failed: 'Lecture text generation failed',
      cancelled: 'Lecture text generation cancelled',
    },
    generate_lecture_audio: {
      queued: 'Audio generation queued...',
      running: 'Generating audio narration...',
      done: 'Audio generated successfully!',
      failed: 'Audio generation failed',
      cancelled: 'Audio generation cancelled',
    },
    generate_lecture_images: {
      queued: 'Lecture image planning queued...',
      running: 'Planning lecture images...',
      done: 'Lecture image generation queued!',
      failed: 'Lecture image planning failed',
      cancelled: 'Lecture image planning cancelled',
    },
    resume_lecture_images: {
      queued: 'Lecture image resume queued...',
      running: 'Planning remaining lecture images...',
      done: 'Remaining lecture image generation queued!',
      failed: 'Lecture image resume failed',
      cancelled: 'Lecture image resume cancelled',
    },
    remap_lecture_images_timeline: {
      queued: 'Lecture image timeline remap queued...',
      running: 'Remapping lecture image timeline...',
      done: 'Lecture image timeline remapped successfully!',
      failed: 'Lecture image timeline remap failed',
      cancelled: 'Lecture image timeline remap cancelled',
    },
    generate_lecture_slide: {
      queued: 'Lecture image generation queued...',
      running: 'Generating lecture image...',
      done: 'Lecture image generated successfully!',
      failed: 'Lecture image generation failed',
      cancelled: 'Lecture image generation cancelled',
    },
    generate_lecture_summary: {
      queued: 'Summary generation queued...',
      running: 'Generating lecture summary...',
      done: 'Summary generated successfully!',
      failed: 'Summary generation failed',
      cancelled: 'Summary generation cancelled',
    },
    generate_topics_for_course: {
      queued: 'Topic generation queued...',
      running: 'Generating course topics...',
      done: 'Topics generated successfully!',
      failed: 'Topic generation failed',
      cancelled: 'Topic generation cancelled',
    },
  }

  const kindMessages = messages[kind]
  return kindMessages ? kindMessages[status] || `${kind} ${status}` : `${kind} ${status}`
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

type MaybeAccessor<T> = T | Accessor<T>

function resolveMaybeAccessor<T>(value: MaybeAccessor<T>): T {
  return typeof value === 'function' ? (value as Accessor<T>)() : value
}

function isTerminalJobStatus(status: JobStatus): boolean {
  return TERMINAL_JOB_STATUSES.has(status)
}

function isActiveJobStatus(status: JobStatus): boolean {
  return ACTIVE_JOB_STATUSES.has(status)
}

function getJobFailureMessage(job: JobRow): string {
  return job.last_error || `Job ${job.status}`
}

export interface JobPollingOptions {
  pollIntervalMs?: number
  timeoutMs?: number
  enabled?: MaybeAccessor<boolean>
  onJobComplete?: (job: JobRow) => void
  onJobFail?: (job: JobRow) => void
}

/**
 * Reactive SolidJS polling primitive for a single job.
 *
 * Polls immediately, then every 2s by default while the job remains queued/running.
 * Polling stops automatically on terminal status, timeout, disabled state, or cleanup.
 */
export function createJobPolling(
  jobId: MaybeAccessor<number | null | undefined>,
  options: JobPollingOptions = {}
) {
  const [job, setJob] = createSignal<JobRow | null>(null)
  const [isPolling, setIsPolling] = createSignal(false)
  const [lastError, setLastError] = createSignal<string | null>(null)
  const [timedOut, setTimedOut] = createSignal(false)

  let timer: ReturnType<typeof setTimeout> | null = null
  let runId = 0

  const pollIntervalMs = () => options.pollIntervalMs ?? DEFAULT_JOB_POLL_INTERVAL_MS
  const timeoutMs = () => options.timeoutMs ?? TIMEOUT_CONFIG.generation
  const enabled = () =>
    options.enabled === undefined ? true : resolveMaybeAccessor(options.enabled)

  const clearTimer = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  const stop = () => {
    runId += 1
    clearTimer()
    setIsPolling(false)
  }

  const status = createMemo(() => job()?.status)
  const isTerminal = createMemo(() => {
    const currentStatus = status()
    return currentStatus ? isTerminalJobStatus(currentStatus) : false
  })

  const scheduleNextPoll = (currentRunId: number, poll: () => void) => {
    clearTimer()
    timer = setTimeout(poll, pollIntervalMs())
    jobDebug.log('state_change', `Scheduled next job poll for run ${String(currentRunId)}`, {
      pollIntervalMs: pollIntervalMs(),
    })
  }

  const startPolling = (currentJobId: number) => {
    const currentRunId = runId + 1
    runId = currentRunId
    clearTimer()
    setJob(null)
    setLastError(null)
    setTimedOut(false)
    setIsPolling(true)

    const deadline = Date.now() + timeoutMs()
    const jobIdLabel = String(currentJobId)

    const poll = () => {
      void (async () => {
        if (currentRunId !== runId) return

        if (Date.now() > deadline) {
          const seconds = Math.round(timeoutMs() / 1000).toString()
          const timeoutMessage = `Job ${jobIdLabel} did not finish within ${seconds}s`
          jobDebug.log('state_change', timeoutMessage, null)
          setLastError(timeoutMessage)
          setTimedOut(true)
          setIsPolling(false)
          return
        }

        try {
          const nextJob = await getJob(currentJobId)
          if (currentRunId !== runId) return

          setJob(nextJob)
          setLastError(null)

          if (nextJob.status === 'done') {
            jobDebug.log('state_change', `Job ${jobIdLabel} completed`, nextJob)
            setIsPolling(false)
            options.onJobComplete?.(nextJob)
            return
          }

          if (nextJob.status === 'failed' || nextJob.status === 'cancelled') {
            const reason = getJobFailureMessage(nextJob)
            jobDebug.log('state_change', `Job ${jobIdLabel} ${nextJob.status}: ${reason}`, nextJob)
            setLastError(reason)
            setIsPolling(false)
            options.onJobFail?.(nextJob)
            return
          }

          if (isActiveJobStatus(nextJob.status)) {
            scheduleNextPoll(currentRunId, poll)
            return
          }

          setIsPolling(false)
        } catch (error) {
          if (currentRunId !== runId) return
          const message = error instanceof Error ? error.message : 'Failed to poll job status'
          jobDebug.log('error', `Failed to poll job ${jobIdLabel}`, error)
          setLastError(message)
          setIsPolling(false)
        }
      })()
    }

    jobDebug.log('state_change', `Started polling job ${jobIdLabel}`, {
      pollIntervalMs: pollIntervalMs(),
      timeoutMs: timeoutMs(),
    })
    poll()
  }

  createEffect(
    on(
      () => [resolveMaybeAccessor(jobId), enabled()] as const,
      ([currentJobId, isEnabled]) => {
        stop()

        if (!isEnabled || currentJobId == null) {
          setJob(null)
          setLastError(null)
          setTimedOut(false)
          return
        }

        startPolling(currentJobId)
      },
      { defer: false }
    )
  )

  onCleanup(stop)

  return {
    job,
    status,
    isPolling,
    isTerminal,
    timedOut,
    lastError,
    stop,
  }
}

export interface WaitForJobOptions {
  pollIntervalMs?: number
  timeoutMs?: number
}

/**
 * Polls the job detail endpoint until the job finishes or fails.
 * Useful when a component immediately needs the job result payload (e.g., generated professor data).
 */
export async function waitForJobResult(
  jobId: number,
  options: WaitForJobOptions = {}
): Promise<JobRow> {
  const pollIntervalMs = options.pollIntervalMs ?? DEFAULT_JOB_POLL_INTERVAL_MS
  const timeoutMs = options.timeoutMs ?? TIMEOUT_CONFIG.generation
  const deadline = Date.now() + timeoutMs
  const jobIdLabel = String(jobId)
  const timeoutLabel = `${timeoutMs.toString()}ms`

  jobDebug.log('state_change', `Waiting for job ${jobIdLabel} (timeout ${timeoutLabel})`, null)

  while (Date.now() <= deadline) {
    const job = await getJob(jobId)

    if (job.status === 'done') {
      jobDebug.log('state_change', `Job ${jobIdLabel} completed`, job)
      return job
    }

    if (job.status === 'failed' || job.status === 'cancelled') {
      const reason = getJobFailureMessage(job)
      jobDebug.log('state_change', `Job ${jobIdLabel} ${job.status}: ${reason}`, job)
      throw new Error(reason)
    }

    await sleep(pollIntervalMs)
  }

  const seconds = Math.round(timeoutMs / 1000).toString()
  const timeoutMessage = `Job ${jobIdLabel} did not finish within ${seconds}s`
  jobDebug.log('state_change', timeoutMessage, null)
  throw new Error(timeoutMessage)
}
