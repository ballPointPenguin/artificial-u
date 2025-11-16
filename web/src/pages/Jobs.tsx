import { createResource, createSignal, For, Show } from 'solid-js'
import { cancelJob, type JobRow, type JobStatus, listJobs } from '../api/services/jobs-service'
import { Button } from '../components/ui'
import { formatDate } from '../utils/formatDate'

const STATUS_STYLES: Record<JobStatus, string> = {
  queued: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200',
  running: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200',
  done: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200',
  cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200',
}

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = createSignal<JobStatus | undefined>(undefined)
  const [cancellingJobId, setCancellingJobId] = createSignal<number | null>(null)

  const [jobsResource, { refetch }] = createResource(
    () => ({
      status: statusFilter(),
      limit: 50,
    }),
    listJobs
  )

  const handleStatusFilter = (status: JobStatus | undefined) => {
    setStatusFilter(status)
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
                        <td class="px-6 py-4 text-sm text-muted max-w-xs truncate">
                          {job.last_error || '-'}
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
    </main>
  )
}
