import {
  batch,
  createEffect,
  createMemo,
  createResource,
  createSignal,
  For,
  onCleanup,
  Show,
  untrack,
} from 'solid-js'
import {
  cancelJob,
  getJob,
  getJobsSummary,
  type JobEvent,
  type JobRow,
  type JobStatus,
  listJobs,
} from '../api/services/jobs-service'
import JobCard from '../components/jobs/JobCard'
import JobErrorModal from '../components/jobs/JobErrorModal'
import JobFilters from '../components/jobs/JobFilters'
import JobStatStrip from '../components/jobs/JobStatStrip'
import { appendPage, applyJobEvent, applySnapshot } from '../components/jobs/job-feed'
import { Alert, Button, ConfirmationModal } from '../components/ui'
import { getJobEventHub } from '../utils/job-events-hub'

const PAGE_SIZE = 25

/**
 * Admin jobs dashboard: stat strip (tappable status filters), kind filter, and
 * a live card feed. The feed is patched in place from SSE events — it is never
 * wholesale refetched while you're looking at it.
 */
export default function JobsPage() {
  const [statusFilter, setStatusFilter] = createSignal<JobStatus | undefined>(undefined)
  const [kindFilter, setKindFilter] = createSignal<string | undefined>(undefined)
  const [jobs, setJobs] = createSignal<JobRow[]>([])
  const [loading, setLoading] = createSignal(true)
  const [loadingMore, setLoadingMore] = createSignal(false)
  const [loadError, setLoadError] = createSignal<string | null>(null)
  const [hasMore, setHasMore] = createSignal(false)
  const [nextBeforeId, setNextBeforeId] = createSignal<number | null>(null)
  const [now, setNow] = createSignal(Date.now())
  const [errorModalJob, setErrorModalJob] = createSignal<JobRow | null>(null)
  const [cancelTarget, setCancelTarget] = createSignal<JobRow | null>(null)
  const [cancelling, setCancelling] = createSignal(false)
  const [actionError, setActionError] = createSignal<string | null>(null)

  const filters = () => ({ status: statusFilter(), kind: kindFilter() })

  const [summary, { refetch: refetchSummary }] = createResource(getJobsSummary)

  let loadRunId = 0
  const loadInitial = async () => {
    const runId = ++loadRunId
    setLoading(true)
    setLoadError(null)
    try {
      const page = await listJobs({ ...filters(), limit: PAGE_SIZE })
      if (runId !== loadRunId) return
      batch(() => {
        setJobs(page.jobs)
        setHasMore(page.has_more)
        setNextBeforeId(page.next_before_id)
      })
    } catch (error) {
      if (runId !== loadRunId) return
      setLoadError(error instanceof Error ? error.message : 'Failed to load jobs')
    } finally {
      if (runId === loadRunId) setLoading(false)
    }
  }

  const loadMore = async () => {
    const beforeId = nextBeforeId()
    if (beforeId == null || loadingMore()) return
    setLoadingMore(true)
    try {
      const page = await listJobs({ ...filters(), limit: PAGE_SIZE, before_id: beforeId })
      batch(() => {
        setJobs((current) => appendPage(current, page.jobs))
        setHasMore(page.has_more)
        setNextBeforeId(page.next_before_id)
      })
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to load more jobs')
    } finally {
      setLoadingMore(false)
    }
  }

  // Initial load + reload whenever a filter changes.
  createEffect(() => {
    filters()
    void loadInitial()
  })

  // Debounced summary refresh after job churn (new jobs or terminal transitions).
  let summaryTimer: ReturnType<typeof setTimeout> | null = null
  const scheduleSummaryRefresh = () => {
    if (summaryTimer) clearTimeout(summaryTimer)
    summaryTimer = setTimeout(() => {
      summaryTimer = null
      void refetchSummary()
    }, 3000)
  }

  // Hydrate provisional rows (jobs first seen via SSE) with one getJob fetch.
  const pendingHydration = new Set<number>()
  const hydrate = (jobId: number) => {
    if (pendingHydration.has(jobId)) return
    pendingHydration.add(jobId)
    getJob(jobId)
      .then((row) => {
        setJobs((current) =>
          current.map((job) => (job.id === row.id ? { ...row, status: job.status } : job))
        )
      })
      .catch(() => {
        // Provisional card simply stays sparse; nothing to do.
      })
      .finally(() => {
        pendingHydration.delete(jobId)
      })
  }

  const hub = getJobEventHub()
  const unsubscribe = hub.subscribe(
    {},
    (event: JobEvent) => {
      const result = applyJobEvent(untrack(jobs), event, untrack(filters))
      setJobs(result.jobs)
      if (result.needsHydration != null) hydrate(result.needsHydration)
      if (event.status !== 'running') scheduleSummaryRefresh()
    },
    (snapshot) => {
      setJobs((current) => applySnapshot(current, snapshot, untrack(filters)))
    }
  )
  onCleanup(() => {
    unsubscribe()
    if (summaryTimer) clearTimeout(summaryTimer)
  })

  // Tick a shared clock while anything is running (live elapsed times).
  const hasRunning = createMemo(() => jobs().some((job) => job.status === 'running'))
  createEffect(() => {
    if (!hasRunning()) return
    const timer = setInterval(() => setNow(Date.now()), 1000)
    onCleanup(() => {
      clearInterval(timer)
    })
  })

  const toggleStatus = (status: JobStatus) => {
    setStatusFilter((current) => (current === status ? undefined : status))
  }

  const confirmCancel = async () => {
    const target = cancelTarget()
    if (!target) return
    setCancelling(true)
    try {
      await cancelJob(target.id)
      setJobs((current) =>
        current.map((job) => (job.id === target.id ? { ...job, status: 'cancelled' } : job))
      )
      setCancelTarget(null)
      scheduleSummaryRefresh()
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to cancel job')
      setCancelTarget(null)
    } finally {
      setCancelling(false)
    }
  }

  return (
    <main class="container mx-auto p-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-display text-shadow-golden">Background Jobs</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            void loadInitial()
            void refetchSummary()
          }}
        >
          Refresh
        </Button>
      </div>

      <JobStatStrip
        summary={summary()}
        activeStatus={statusFilter()}
        onToggleStatus={toggleStatus}
      />

      <JobFilters
        kind={kindFilter()}
        onKindChange={setKindFilter}
        kindStats={summary()?.kinds_recent}
      />

      <Show when={actionError()}>
        <div class="mb-4">
          <Alert variant="danger">
            <div class="flex items-center justify-between gap-2">
              <span>{actionError()}</span>
              <Button variant="ghost" size="sm" onClick={() => setActionError(null)}>
                ✕
              </Button>
            </div>
          </Alert>
        </div>
      </Show>

      <Show when={!loading()} fallback={<p class="text-muted text-center py-8">Loading jobs…</p>}>
        <Show
          when={!loadError()}
          fallback={
            <div class="text-danger text-center py-8">
              <p>Error loading jobs: {loadError()}</p>
              <Button variant="ghost" onClick={() => void loadInitial()} class="mt-4">
                Retry
              </Button>
            </div>
          }
        >
          <Show
            when={jobs().length > 0}
            fallback={<div class="text-center py-8 text-muted">No jobs found</div>}
          >
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              <For each={jobs()}>
                {(job) => (
                  <JobCard
                    job={job}
                    now={now()}
                    onShowError={setErrorModalJob}
                    onCancel={setCancelTarget}
                  />
                )}
              </For>
            </div>
            <Show when={hasMore()}>
              <Button
                variant="outline"
                class="w-full mt-4"
                onClick={() => void loadMore()}
                disabled={loadingMore()}
              >
                {loadingMore() ? 'Loading…' : 'Load more'}
              </Button>
            </Show>
            <div class="mt-3 text-xs text-muted text-center">Showing {jobs().length} jobs</div>
          </Show>
        </Show>
      </Show>

      <JobErrorModal job={errorModalJob()} onClose={() => setErrorModalJob(null)} />

      <ConfirmationModal
        isOpen={cancelTarget() !== null}
        title="Cancel job"
        message={
          <>
            Cancel {cancelTarget()?.kind} #{cancelTarget()?.id}?
          </>
        }
        confirmText="Cancel job"
        cancelText="Keep running"
        onConfirm={() => void confirmCancel()}
        onCancel={() => setCancelTarget(null)}
        isConfirming={cancelling()}
      />
    </main>
  )
}
