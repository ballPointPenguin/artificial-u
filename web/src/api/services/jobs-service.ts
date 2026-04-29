import { httpClient } from '../client'
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
  /** Wall-clock execution time of the last attempt, when available (from worker telemetry). */
  duration_ms?: number | null
  payload?: unknown
  parent_job_id?: number | null
  created_at?: string
  updated_at?: string
}

export async function getJob(jobId: number): Promise<JobRow> {
  return httpClient.get<JobRow>(ENDPOINTS.jobs.detail(jobId))
}

export async function listJobs(params?: {
  status?: JobStatus
  limit?: number
  kind?: string
  lecture_id?: number
  topic_id?: number
  course_id?: number
  parent_id?: number
}): Promise<JobRow[]> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.kind) qs.set('kind', params.kind)
  if (params?.lecture_id != null) qs.set('lecture_id', String(params.lecture_id))
  if (params?.topic_id != null) qs.set('topic_id', String(params.topic_id))
  if (params?.course_id != null) qs.set('course_id', String(params.course_id))
  if (params?.parent_id != null) qs.set('parent_id', String(params.parent_id))
  const endpoint = `${ENDPOINTS.jobs.list}${qs.toString() ? `?${qs.toString()}` : ''}`
  return httpClient.get<JobRow[]>(endpoint)
}

export async function listJobChildren(parentJobId: number): Promise<JobRow[]> {
  return httpClient.get<JobRow[]>(`${ENDPOINTS.jobs.detail(parentJobId)}/children`)
}

export async function cancelJob(jobId: number): Promise<{ id: number; status: string }> {
  const endpoint = ENDPOINTS.jobs.cancel(jobId)
  return httpClient.post<{ id: number; status: string }>(endpoint, {})
}

// Shared event-shaped job payload used by SSE and polling callbacks.
export type JobEvent = {
  id: number
  kind: string
  status: JobStatus
  payload?: unknown
  result?: unknown
  last_error?: string
}
