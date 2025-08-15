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

  const query = qs.toString()
  const base = ENDPOINTS.jobs.stream
  const path = query ? `${base}?${query}` : base
  const url = createUrl(path)
  const es = new EventSource(url)
  es.addEventListener('job', (ev) => {
    try {
      const me = ev as MessageEvent<string>
      const raw: string = typeof me.data === 'string' ? me.data : String(me.data)
      const parsed = JSON.parse(raw) as unknown
      const data = parsed as JobEvent
      onEvent(data)
    } catch {
      // ignore malformed
    }
  })
  return () => {
    es.close()
  }
}
