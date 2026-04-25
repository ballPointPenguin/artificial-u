import { createResource, createSignal, For, onCleanup, Show } from 'solid-js'
import {
  cancelJob,
  type JobEvent,
  type JobRow,
  type JobStatus,
  listJobs,
} from '../api/services/jobs-service'
import { Button } from '../components/ui'
import { formatDate } from '../utils/formatDate'
import { getJobEventHub } from '../utils/job-events-hub'

const STATUS_STYLES: Record<JobStatus, string> = {
  queued: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200',
  running: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200',
  done: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200',
  cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200',
}

function durationMsFromResult(r: unknown): number | null {
  if (!r || typeof r !== 'object') return null
  const o = r as { _job_telemetry?: { duration_ms?: number } }
  const ms = o._job_telemetry?.duration_ms
  return typeof ms === 'number' && !Number.isNaN(ms) ? ms : null
}

/** Display whole seconds for readability (from duration_ms). */
function formatRunDurationSeconds(ms: number | null | undefined): string {
  if (ms == null) return '-'
  const sec = Math.round(ms / 1000)
  return `${String(sec)}s`
}

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = createSignal<JobStatus | undefined>(undefined)
  const [cancellingJobId, setCancellingJobId] = createSignal<number | null>(null)
  const [errorModalJob, setErrorModalJob] = createSignal<JobRow | null>(null)

  const [jobsResource, { refetch, mutate }] = createResource(
    () => ({
      status: statusFilter(),
      limit: 50,
    }),
    listJobs
  )

  // Subscribe to SSE updates for real-time job status
  const hub = getJobEventHub()
  const unsubscribe = hub.subscribe({}, (event: JobEvent) => {
    // Update the job in the list when we receive an event
    mutate((jobs) => {
      if (!jobs) return jobs

      const jobIndex = jobs.findIndex((j) => j.id === event.id)

      if (jobIndex === -1) {
        // New job - refetch to get it
        void refetch()
        return jobs
      }

      // Update existing job
      const updatedJobs = [...jobs]
      const fromEvent = event.result != null ? durationMsFromResult(event.result) : null
      updatedJobs[jobIndex] = {
        ...updatedJobs[jobIndex],
        status: event.status,
        last_error: event.last_error || updatedJobs[jobIndex].last_error,
        result: event.result !== undefined ? event.result : updatedJobs[jobIndex].result,
        duration_ms: fromEvent != null ? fromEvent : updatedJobs[jobIndex].duration_ms,
      }

      return updatedJobs
    })
  })

  onCleanup(() => {
    unsubscribe()
  })

  const handleStatusFilter = (status: JobStatus | undefined) => {
    setStatusFilter(status)
  }

  const extractParams = (job: JobRow): string => {
    const payload = job.payload as Record<string, unknown> | undefined
    if (!payload) return '-'

    const params: string[] = []

    const safeString = (value: unknown): string | null => {
      if (value === null || value === undefined) return null
      if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        return String(value)
      }
      return null
    }

    const lectureId = safeString(payload.lecture_id)
    if (lectureId) {
      params.push(`lecture: ${lectureId}`)
    }

    const topicId = safeString(payload.topic_id)
    if (topicId) {
      params.push(`topic: ${topicId}`)
    } else if (payload.partial_attributes && typeof payload.partial_attributes === 'object') {
      const partialAttrs = payload.partial_attributes as Record<string, unknown>
      const partialTopicId = safeString(partialAttrs.topic_id)
      if (partialTopicId) {
        params.push(`topic: ${partialTopicId}`)
      }
    }

    const courseId = safeString(payload.course_id)
    if (courseId) {
      params.push(`course: ${courseId}`)
    } else if (payload.partial_attributes && typeof payload.partial_attributes === 'object') {
      const partialAttrs = payload.partial_attributes as Record<string, unknown>
      const partialCourseId = safeString(partialAttrs.course_id)
      if (partialCourseId) {
        params.push(`course: ${partialCourseId}`)
      }
    }

    return params.length > 0 ? params.join(', ') : '-'
  }

  const handleCancelJob = async (jobId: number) => {
    if (!confirm('Are you sure you want to cancel this job?')) {
      return
    }

    setCancellingJobId(jobId)
    try {
      await cancelJob(jobId)
      void refetch() // Refresh the job list
    } catch (error) {
      console.error('Failed to cancel job:', error)
      alert('Failed to cancel job. Please try again.')
    } finally {
      setCancellingJobId(null)
    }
  }

  return (
    <main class="container mx-auto p-4">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-display mb-6 text-parchment-100 text-shadow-golden">
          Background Jobs
        </h1>
        <Button variant="secondary" onClick={() => void refetch()}>
          Refresh
        </Button>
      </div>

      {/* Status Filters */}
      <div class="mb-6 flex flex-wrap gap-2">
        <Button
          variant={statusFilter() === undefined ? 'primary' : 'outline'}
          onClick={() => {
            handleStatusFilter(undefined)
          }}
        >
          All
        </Button>
        <Button
          variant={statusFilter() === 'queued' ? 'primary' : 'outline'}
          onClick={() => {
            handleStatusFilter('queued')
          }}
        >
          Queued
        </Button>
        <Button
          variant={statusFilter() === 'running' ? 'primary' : 'outline'}
          onClick={() => {
            handleStatusFilter('running')
          }}
        >
          Running
        </Button>
        <Button
          variant={statusFilter() === 'done' ? 'primary' : 'outline'}
          onClick={() => {
            handleStatusFilter('done')
          }}
        >
          Done
        </Button>
        <Button
          variant={statusFilter() === 'failed' ? 'primary' : 'outline'}
          onClick={() => {
            handleStatusFilter('failed')
          }}
        >
          Failed
        </Button>
        <Button
          variant={statusFilter() === 'cancelled' ? 'primary' : 'outline'}
          onClick={() => {
            handleStatusFilter('cancelled')
          }}
        >
          Cancelled
        </Button>
      </div>

      {/* Jobs Table */}
      <Show
        when={!jobsResource.loading}
        fallback={<p class="text-muted text-center py-8">Loading jobs...</p>}
      >
        <Show
          when={!jobsResource.error}
          fallback={
            <div class="text-danger text-center py-8">
              <p>
                Error loading jobs:{' '}
                {jobsResource.error instanceof Error ? jobsResource.error.message : 'Unknown error'}
              </p>
              <Button variant="ghost" onClick={() => void refetch()} class="mt-4">
                Retry
              </Button>
            </div>
          }
        >
          <Show
            when={jobsResource()?.length}
            fallback={<div class="text-center py-8">No jobs found</div>}
          >
            <div class="arcane-card overflow-x-auto">
              <table class="min-w-full divide-y divide-border">
                <thead class="bg-muted/50">
                  <tr>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      ID
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Kind
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Status
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Attempts
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Priority
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Created
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Updated
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Run time
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Params
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Error
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-background divide-y divide-border">
                  <For each={jobsResource()}>
                    {(job: JobRow) => (
                      <tr class="hover:bg-muted/30 transition-colors">
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">{job.id}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">{job.kind}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                          <span
                            class={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${STATUS_STYLES[job.status]}`}
                          >
                            {job.status}
                          </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                          {job.attempts} / {job.max_attempts}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">{job.priority ?? 0}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-muted">
                          {job.created_at ? formatDate(new Date(job.created_at)) : '-'}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-muted">
                          {job.updated_at ? formatDate(new Date(job.updated_at)) : '-'}
                        </td>
                        <td
                          class="px-6 py-4 whitespace-nowrap text-sm text-muted"
                          title={
                            job.duration_ms != null ? `${String(job.duration_ms)} ms` : undefined
                          }
                        >
                          {formatRunDurationSeconds(
                            job.duration_ms ?? durationMsFromResult(job.result)
                          )}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-muted">
                          {extractParams(job)}
                        </td>
                        <td class="px-6 py-4 text-sm text-muted">
                          <Show when={job.last_error} fallback={<span class="text-muted">-</span>}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setErrorModalJob(job)}
                              class="text-red-600 hover:text-red-700"
                            >
                              View Error
                            </Button>
                          </Show>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                          <Show when={job.status === 'queued' || job.status === 'running'}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => void handleCancelJob(job.id)}
                              disabled={cancellingJobId() === job.id}
                            >
                              {cancellingJobId() === job.id ? 'Cancelling...' : 'Cancel'}
                            </Button>
                          </Show>
                        </td>
                      </tr>
                    )}
                  </For>
                </tbody>
              </table>
            </div>
            <div class="mt-4 text-sm text-muted">
              Showing {jobsResource()?.length ?? 0} jobs (limit: 50)
            </div>
          </Show>
        </Show>
      </Show>

      {/* Error Modal */}
      <Show when={errorModalJob()}>
        <div
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => setErrorModalJob(null)}
        >
          <div
            class="arcane-card max-w-3xl max-h-[80vh] w-full mx-4 overflow-hidden flex flex-col"
            onClick={(e) => {
              e.stopPropagation()
            }}
          >
            <div class="flex items-center justify-between p-6 border-b border-border">
              <h2 class="text-xl font-display">
                Job Error - {errorModalJob()?.kind} #{errorModalJob()?.id}
              </h2>
              <Button variant="ghost" size="sm" onClick={() => setErrorModalJob(null)}>
                ✕
              </Button>
            </div>
            <div class="p-6 overflow-auto">
              <pre class="text-xs font-mono bg-muted/50 p-4 rounded overflow-x-auto whitespace-pre-wrap break-words">
                {errorModalJob()?.last_error || 'No error message available'}
              </pre>
            </div>
            <div class="flex justify-end gap-2 p-6 border-t border-border">
              <Button variant="secondary" onClick={() => setErrorModalJob(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      </Show>
    </main>
  )
}
