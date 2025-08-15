import { createUrl, httpClient } from '../client'
import { ENDPOINTS } from '../config'

export type JobStatus = 'queued' | 'running' | 'done' | 'failed' | 'cancelled'

export interface JobRow {
  id: number
  kind: string
  status: JobStatus
  attempts: number
  max_attempts: number
  priority?: number
  run_after?: string
  last_error?: string | null
  result?: unknown
  created_at?: string
  updated_at?: string
}

export async function listJobs(params?: { status?: JobStatus; limit?: number }): Promise<JobRow[]> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.limit) qs.set('limit', String(params.limit))
  const endpoint = `${ENDPOINTS.jobs.list}${qs.toString() ? `?${qs.toString()}` : ''}`
  return httpClient.get<JobRow[]>(endpoint)
}

export async function getJob(jobId: number): Promise<JobRow> {
  return httpClient.get<JobRow>(ENDPOINTS.jobs.detail(jobId))
}

export async function getJobsSummary(): Promise<Record<JobStatus, number>> {
  return httpClient.get<Record<JobStatus, number>>(ENDPOINTS.jobs.summary)
}

// SSE subscription helper for job events
export type JobEvent = {
  id: number
  kind: string
  status: JobStatus | 'cancelled'
  payload?: unknown
  result?: unknown
  last_error?: string
}

// Shared EventSource manager keyed by query string so we only open one SSE per unique stream
type Listener = (e: JobEvent) => void

const sseRegistry = new Map<string, { es: EventSource; listeners: Set<Listener> }>()

export function subscribeJobEvents(
  params: { lecture_id?: number; topic_id?: number; kinds?: string[] },
  onEvent: (e: JobEvent) => void
) {
  const qs = new URLSearchParams()
  if (params.lecture_id != null) qs.set('lecture_id', String(params.lecture_id))
  if (params.topic_id != null) qs.set('topic_id', String(params.topic_id))
  if (params.kinds && params.kinds.length > 0) {
    params.kinds.forEach((k) => {
      qs.append('kinds', k)
    })
  }

  const base = ENDPOINTS.jobs.stream
  const query = qs.toString()
  const path = query ? `${base}?${query}` : base
  const url = createUrl(path)

  // Reuse or create EventSource per URL key
  let entry = sseRegistry.get(url)
  if (!entry) {
    const es = new EventSource(url)
    const listeners = new Set<Listener>()
    // Route only 'job' events to registered listeners
    es.addEventListener('job', (ev) => {
      try {
        const me = ev as MessageEvent<string>
        const raw: string = typeof me.data === 'string' ? me.data : String(me.data)
        const data = JSON.parse(raw) as JobEvent
        listeners.forEach((fn) => {
          fn(data)
        })
      } catch {
        // ignore
      }
    })
    // Keep quiet on errors; the browser auto-reconnects EventSource
    es.onerror = () => {
      // noop
    }
    entry = { es, listeners }
    sseRegistry.set(url, entry)
  }

  entry.listeners.add(onEvent)

  // Return unsubscribe; close actual EventSource when last listener unsubscribes
  return () => {
    const e = sseRegistry.get(url)
    if (!e) return
    e.listeners.delete(onEvent)
    if (e.listeners.size === 0) {
      e.es.close()
      sseRegistry.delete(url)
    }
  }
}
