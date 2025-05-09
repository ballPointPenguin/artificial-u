/**
 * Lecture service
 */
import { createUrl, httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type {
  AudioRedirectResponse,
  Lecture,
  LectureCreate,
  LectureGenerateRequest,
  LectureList,
  LectureUpdate,
} from '../types'

interface GetLecturesParams {
  page?: number
  size?: number
  course_id?: number
  professor_id?: number
  status?: string
  title?: string
  date_from?: string
  date_to?: string
}

/**
 * Get a paginated list of lectures
 */
export async function getLectures(params: GetLecturesParams = {}): Promise<LectureList> {
  const queryParams = new URLSearchParams()

  if (params.page) queryParams.append('page', String(params.page))
  if (params.size) queryParams.append('size', String(params.size))
  if (params.course_id) queryParams.append('course_id', String(params.course_id))
  if (params.professor_id) queryParams.append('professor_id', String(params.professor_id))
  if (params.status) queryParams.append('status', params.status)
  if (params.title) queryParams.append('title', params.title)
  if (params.date_from) queryParams.append('date_from', params.date_from)
  if (params.date_to) queryParams.append('date_to', params.date_to)

  const queryString = queryParams.toString()
  const endpoint = `${ENDPOINTS.lectures.list}${queryString ? `?${queryString}` : ''}`

  return httpClient.get<LectureList>(endpoint)
}

/**
 * Get a lecture by ID
 */
export async function getLecture(id: number): Promise<Lecture> {
  return httpClient.get<Lecture>(ENDPOINTS.lectures.detail(id))
}

/**
 * Create a new lecture
 */
export async function createLecture(
  data: Omit<Lecture, 'id' | 'created_at' | 'updated_at'>
): Promise<Lecture> {
  return httpClient.post<Lecture>(ENDPOINTS.lectures.list, data)
}

/**
 * Update a lecture
 */
export async function updateLecture(
  id: number,
  data: Partial<Omit<Lecture, 'id' | 'created_at' | 'updated_at'>>
): Promise<Lecture> {
  return httpClient.put<Lecture>(ENDPOINTS.lectures.detail(id), data)
}

/**
 * Delete a lecture
 */
export async function deleteLecture(id: number): Promise<Record<string, never>> {
  return httpClient.delete<Record<string, never>>(ENDPOINTS.lectures.detail(id))
}

/**
 * Get content of a lecture
 */
export async function getLectureContent(id: number): Promise<string> {
  const url = createUrl(ENDPOINTS.lectures.content(id))
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(
      `Failed to fetch lecture content: ${response.statusText} (status: ${String(response.status)})`
    )
  }
  return response.text()
}

/**
 * Get audio of a lecture, returns redirect URL
 */
export async function getLectureAudio(id: number): Promise<{ url: string }> {
  return httpClient.get<{ url: string }>(ENDPOINTS.lectures.audio(id))
}

/**
 * Download lecture content as text file
 */
export async function downloadLectureContent(id: number): Promise<string> {
  const url = createUrl(ENDPOINTS.lectures.download(id))
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(
      `Failed to download lecture content: ${response.statusText} (status: ${String(response.status)})`
    )
  }
  return response.text()
}

// Add LectureGeneratePayload for generating lectures via AI
interface LectureGeneratePayload {
  partial_attributes?: Record<string, unknown>
  freeform_prompt?: string
}

/**
 * Generate lecture data using AI
 */
export async function generateLecture(data: LectureGeneratePayload): Promise<Lecture> {
  return httpClient.post<Lecture>(ENDPOINTS.lectures.generate, data)
}

interface ListLecturesParams {
  page: number
  size: number
  courseId?: number
  professorId?: number
  search?: string
}

export const lectureService = {
  listLectures: (params: ListLecturesParams): Promise<LectureList> => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      size: params.size.toString(),
    })
    if (params.courseId) queryParams.set('course_id', params.courseId.toString())
    if (params.professorId) queryParams.set('professor_id', params.professorId.toString())
    if (params.search) queryParams.set('search', params.search)

    return httpClient.get<LectureList>(`${ENDPOINTS.lectures.list}?${queryParams.toString()}`)
  },

  getLecture: (lectureId: number): Promise<Lecture> => {
    return httpClient.get<Lecture>(ENDPOINTS.lectures.detail(lectureId))
  },

  getLectureContent: async (lectureId: number): Promise<string> => {
    const url = createUrl(ENDPOINTS.lectures.content(lectureId))
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(
        `Failed to fetch lecture content: ${response.statusText} (status: ${String(response.status)})`
      )
    }
    return response.text()
  },

  getLectureAudioUrl: (lectureId: number): Promise<AudioRedirectResponse> => {
    return httpClient.get<AudioRedirectResponse>(ENDPOINTS.lectures.audio(lectureId))
  },

  createLecture: (data: LectureCreate): Promise<Lecture> => {
    return httpClient.post<Lecture>(ENDPOINTS.lectures.list, data)
  },

  updateLecture: (lectureId: number, data: LectureUpdate): Promise<Lecture> => {
    return httpClient.patch<Lecture>(ENDPOINTS.lectures.detail(lectureId), data)
  },

  deleteLecture: (lectureId: number): Promise<null> => {
    return httpClient.delete<null>(ENDPOINTS.lectures.detail(lectureId))
  },

  downloadLectureContent: async (lectureId: number): Promise<string> => {
    const url = createUrl(ENDPOINTS.lectures.download(lectureId))
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(
        `Failed to download lecture content: ${response.statusText} (status: ${String(response.status)})`
      )
    }
    return response.text()
  },

  generateLecture: (data: LectureGenerateRequest): Promise<Lecture> => {
    return httpClient.post<Lecture>(ENDPOINTS.lectures.generate, data)
  },
}
