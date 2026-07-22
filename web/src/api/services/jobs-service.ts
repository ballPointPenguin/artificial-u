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
  /** Best-effort model name for this job's kind (e.g. "claude-sonnet-4-6"), when one is obvious. */
  model?: string | null
  /** Relative frontend path to the lecture or topic this job concerns, when resolvable. */
  link_path?: string | null
}

export interface JobListPage {
  jobs: JobRow[]
  has_more: boolean
  /** Pass as before_id to fetch the next (older) page; null on the last page. */
  next_before_id: number | null
}

export interface JobKindStat {
  kind: string
  count: number
  avg_duration_ms: number | null
  p50_duration_ms: number | null
}

export interface JobsSummary {
  counts: Partial<Record<JobStatus, number>>
  avg_wait_seconds: number
  failed_last_hour: number
  window_hours: number
  kinds_recent: JobKindStat[]
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
  before_id?: number
}): Promise<JobListPage> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.kind) qs.set('kind', params.kind)
  if (params?.lecture_id != null) qs.set('lecture_id', String(params.lecture_id))
  if (params?.topic_id != null) qs.set('topic_id', String(params.topic_id))
  if (params?.course_id != null) qs.set('course_id', String(params.course_id))
  if (params?.parent_id != null) qs.set('parent_id', String(params.parent_id))
  if (params?.before_id != null) qs.set('before_id', String(params.before_id))
  const endpoint = `${ENDPOINTS.jobs.list}${qs.toString() ? `?${qs.toString()}` : ''}`
  return httpClient.get<JobListPage>(endpoint)
}

export async function getJobsSummary(): Promise<JobsSummary> {
  return httpClient.get<JobsSummary>(ENDPOINTS.jobs.summary)
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
