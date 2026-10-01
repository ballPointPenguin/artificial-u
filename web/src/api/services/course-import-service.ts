import { httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type { JobRow } from './jobs-service'

export type CourseCodeAction = 'replace' | 'rename' | 'cancel'

export interface ImportResolutions {
  course_code?: CourseCodeAction
  new_code?: string
  professor?: 'reuse' | 'create'
  professor_id?: number
  hidden?: boolean
}

export interface ImportPlan {
  export_version: string
  exported_at?: string | null
  course: {
    code: string
    title: string
    language?: string | null
    status?: string | null
    topics: number
    lectures: number
  }
  assets: Record<string, number>
  tags: string[]
  course_code_conflict: {
    existing: {
      id: number
      code: string
      title: string
      professor_name: string | null
      lecture_count: number
      status: string
      updated_at: string | null
    }
    same_title: boolean
    options: CourseCodeAction[]
    suggested_code: string
  } | null
  department: {
    action: 'match' | 'create' | 'none'
    name?: string
    code?: string
    match?: { id: number; name: string; code: string; matched_by: string } | null
  }
  professor: {
    action: 'reuse' | 'create' | 'none'
    name?: string
    title?: string | null
    specialization?: string | null
    candidates?: {
      id: number
      name: string
      title: string | null
      specialization: string | null
      department: string | null
    }[]
  }
  voices: { name: string | null; tts_backend: string; action: 'match' | 'create' | 'skip' }[]
  connected_courses: { found: string[]; missing: string[] }
  warnings: string[]
}

export interface ImportAnalysis {
  upload_key: string
  plan: ImportPlan
}

/** Large archives can take a while to upload. */
const UPLOAD_TIMEOUT_MS = 10 * 60 * 1000

export const courseImportService = {
  analyze: (file: File): Promise<ImportAnalysis> => {
    const formData = new FormData()
    formData.append('file', file)
    return httpClient.postFormData<ImportAnalysis>(
      ENDPOINTS.courses.importAnalyze,
      formData,
      UPLOAD_TIMEOUT_MS
    )
  },

  start: (uploadKey: string, resolutions: ImportResolutions): Promise<JobRow> => {
    return httpClient.post<JobRow>(ENDPOINTS.courses.import, {
      upload_key: uploadKey,
      resolutions,
    })
  },
}
