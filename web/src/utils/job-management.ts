/**
 * Centralized job management utilities for tracking background jobs
 * and their states across components.
 */

import { createEffect, createSignal, on, onCleanup } from 'solid-js'
import { TIMEOUT_CONFIG } from '../api/config.js'
import { getJob, type JobEvent, type JobRow, listJobs } from '../api/services/jobs-service.js'
import { useAuth } from '../auth/AuthProvider.js'
import { jobDebug } from './job-debug.js'
import { getJobEventHub } from './job-events-hub.js'

export interface JobTrackerOptions {
  topicId?: () => number | undefined
  lectureId?: () => number | undefined
  courseId?: () => number | undefined
  kinds?: string[]
  onJobComplete?: (event: JobEvent) => void
  onJobStart?: (event: JobEvent) => void
  onJobFail?: (event: JobEvent) => void
}

/**
 * Creates a reactive job tracker that monitors job status via SSE
 * and provides consolidated state management.
 */
export function createJobTracker(options: JobTrackerOptions) {
  const auth = useAuth()

  const [activeJobIds, setActiveJobIds] = createSignal<Set<number>>(new Set())
  const [isInitializing, setIsInitializing] = createSignal(true)
  const [lastError, setLastError] = createSignal<string | null>(null)

  let unsubscribe: (() => void) | null = null

  // Computed signal for whether any jobs are active
  const hasActiveJobs = () => activeJobIds().size > 0

  // Get initial values for SSE subscription (will be updated as dependencies change)
  let initialTopicId = options.topicId?.()
  let initialLectureId = options.lectureId?.()
  let initialCourseId = options.courseId?.()

  // Debug logging
  jobDebug.log('subscription', 'JobTracker initializing', {
    topicId: initialTopicId,
    lectureId: initialLectureId,
    courseId: initialCourseId,
    kinds: options.kinds,
  })

  // Track reactive changes and restart SSE when dependencies change
  createEffect(
    on(
      // Track these reactive values
      () =>
        [
          auth.isAuthenticated(),
          options.topicId?.(),
          options.lectureId?.(),
          options.courseId?.(),
        ] as const,
      async ([isAuthed, topicId, lectureId, courseId]) => {
        // Clean up previous subscription
        if (unsubscribe) {
          jobDebug.log('subscription', 'Dependencies changed, unsubscribing previous SSE', {
            topicId,
            lectureId,
            courseId,
            wasTopicId: initialTopicId,
            wasLectureId: initialLectureId,
          })
          unsubscribe()
          unsubscribe = null
        }

        if (!isAuthed) {
          jobDebug.log(
            'subscription',
            'Skipping job subscription because user is not authenticated',
            null
          )
          setIsInitializing(false)
          setActiveJobIds(new Set<number>())
          setLastError(null)
          return
        }

        // Update initial values for the new effect run
        initialTopicId = topicId
        initialLectureId = lectureId
        initialCourseId = courseId

        // Skip if no valid IDs
        if (!topicId && !lectureId && !courseId) {
          setIsInitializing(false)
          setActiveJobIds(new Set<number>())
          return
        }

        // Reset state for new entity
        setIsInitializing(true)
        setActiveJobIds(new Set<number>())
        setLastError(null)

        // Load initial job snapshot
        try {
          const [inflight, queued] = await Promise.all([
            listJobs({
              status: 'running',
              topic_id: topicId,
              lecture_id: lectureId,
              course_id: courseId,
            }),
            listJobs({
              status: 'queued',
              topic_id: topicId,
              lecture_id: lectureId,
              course_id: courseId,
            }),
          ])

          const ids = new Set<number>()
          for (const job of [...inflight, ...queued]) {
            // Filter by kinds if specified
            if (!options.kinds || options.kinds.includes(job.kind)) {
              ids.add(job.id)
              jobDebug.log('state_change', `Found active job: ${job.kind} #${String(job.id)}`, {
                id: job.id,
                kind: job.kind,
                status: job.status,
              })
            }
          }
          setActiveJobIds(ids)
        } catch (error) {
          jobDebug.log('error', 'Failed to initialize job tracker', error)
          setLastError('Failed to load job status')
        } finally {
          setIsInitializing(false)
        }

        // Subscribe to job events via the hub
        const hub = getJobEventHub()
        const filter = {
          topicId,
          lectureId,
          courseId,
          kinds: options.kinds,
        }

        jobDebug.log('subscription', 'Subscribing via JobEventHub', filter)

        unsubscribe = hub.subscribe(
          filter,
          (event) => {
            const { status } = event

            jobDebug.log(
              'event',
              `Hub event: ${event.kind} #${String(event.id)} - ${status}`,
              event
            )

            // Update active job tracking
            setActiveJobIds((prev) => {
              const newIds = new Set(prev)
              if (status === 'queued' || status === 'running') {
                newIds.add(event.id)
                options.onJobStart?.(event)
              } else {
                newIds.delete(event.id)
                if (status === 'done') {
                  jobDebug.log(
                    'state_change',
                    `Job completed: ${event.kind} #${String(event.id)}`,
                    event
                  )
                  options.onJobComplete?.(event)
                } else if (status === 'failed') {
                  options.onJobFail?.(event)
                  setLastError(`Job ${event.kind} failed`)
                }
              }
              return newIds
            })
          },
          (jobs) => {
            const ids = new Set<number>()
            for (const job of jobs) {
              if (job.status === 'queued' || job.status === 'running') {
                ids.add(job.id)
              }
            }
            jobDebug.log('state_change', 'Reconciled active jobs from SSE snapshot', {
              activeJobIds: [...ids],
            })
            setActiveJobIds(ids)
          }
        )
      },
      { defer: false } // Run immediately, not deferred
    )
  )

  // Cleanup on unmount
  onCleanup(() => {
    jobDebug.log('subscription', 'Cleaning up SSE subscription', null)
    if (unsubscribe) {
      unsubscribe()
    }
  })

  return {
    hasActiveJobs,
    activeJobIds,
    isInitializing,
    lastError,
    clearError: () => setLastError(null),
  }
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
  const pollIntervalMs = options.pollIntervalMs ?? 2000
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
      const reason = job.last_error || `Job ${job.status}`
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
