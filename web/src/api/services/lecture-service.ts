/**
 * Lecture service
 */
import { httpClient } from '../client'
import { ENDPOINTS, TIMEOUT_CONFIG } from '../config'
import type {
  AdminLectureListResponse,
  Lecture,
  LectureCreate,
  LectureGenerateRequest,
  LectureList,
  LectureUpdate,
  RecentLecture,
} from '../types'

interface ListLecturesParams {
  page: number
  size: number
  courseId?: number
  professorId?: number
  topicId?: number
  search?: string
}

interface ListAdminLecturesParams {
  page: number
  size: number
  courseId?: number
  courseCode?: string
  sortBy?: string
  order?: 'asc' | 'desc'
}

export const lectureService = {
  listLectures: (params: ListLecturesParams): Promise<LectureList> => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      size: params.size.toString(),
    })
    if (params.courseId) queryParams.set('course_id', params.courseId.toString())
    if (params.professorId) queryParams.set('professor_id', params.professorId.toString())
    if (params.topicId) queryParams.set('topic_id', params.topicId.toString())
    if (params.search) queryParams.set('search', params.search)

    return httpClient.get<LectureList>(`${ENDPOINTS.lectures.list}?${queryParams.toString()}`)
  },

  listAdminLectures: (params: ListAdminLecturesParams): Promise<AdminLectureListResponse> => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      size: params.size.toString(),
    })
    if (params.courseId) queryParams.set('course_id', params.courseId.toString())
    if (params.courseCode) queryParams.set('course_code', params.courseCode)
    if (params.sortBy) queryParams.set('sort_by', params.sortBy)
    if (params.order) queryParams.set('order', params.order)

    return httpClient.get<AdminLectureListResponse>(
      `${ENDPOINTS.lectures.adminList}?${queryParams.toString()}`
    )
  },

  getLecture: (lectureId: number): Promise<Lecture> => {
    return httpClient.get<Lecture>(ENDPOINTS.lectures.detail(lectureId))
  },

  /**
   * Enqueue lecture audio generation job (async). Returns a job stub with id.
   */
  enqueueGenerateLectureAudio: (
    lectureId: number
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.lectures.enqueueGenerateAudio(lectureId), undefined)
  },

  /**
   * Enqueue lecture timeline generation job (async). Returns a job stub with id.
   */
  enqueueGenerateLectureTimeline: (
    lectureId: number
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.lectures.enqueueGenerateTimeline(lectureId), undefined)
  },

  /**
   * Enqueue lecture images generation job (async). Returns a job stub with id.
   */
  enqueueGenerateLectureImages: (
    lectureId: number
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.lectures.enqueueGenerateImages(lectureId), undefined)
  },

  /**
   * Enqueue incomplete lecture image generation resume job (async).
   */
  enqueueResumeLectureImages: (
    lectureId: number
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.lectures.enqueueResumeImages(lectureId), undefined)
  },

  recreateLectureTranscript: (lectureId: number): Promise<Lecture> => {
    return httpClient.post<Lecture>(ENDPOINTS.lectures.recreateTranscript(lectureId), undefined)
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

  /**
   * Enqueue lecture generation job (async). Returns a job stub with id.
   */
  enqueueGenerateLecture: (
    data: LectureGenerateRequest
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.lectures.enqueueGenerate, data)
  },

  /**
   * Enqueue lecture text generation job (async). Returns a job stub with id.
   * This job will generate only the lecture text without triggering audio/summary jobs.
   */
  enqueueGenerateLectureTextOnly: (
    data: LectureGenerateRequest
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.lectures.enqueueGenerateTextOnly, data)
  },

  /**
   * Upload an audio file for a lecture (admin only).
   * Uses FormData to send the file as multipart/form-data.
   */
  uploadAudio: async (lectureId: number, file: File): Promise<Lecture> => {
    const formData = new FormData()
    formData.append('file', file)

    // httpClient.postFormData handles auth, error handling, and timeout
    return httpClient.postFormData<Lecture>(
      ENDPOINTS.lectures.uploadAudio(lectureId),
      formData,
      TIMEOUT_CONFIG.upload
    )
  },

  /**
   * Trigger generation of lecture summary. No body required.
   * Uses extended timeout similar to other generation actions.
   */
  generateSummary: (lectureId: number, onTimeout?: () => void): Promise<Lecture> => {
    return httpClient.postWithExtendedTimeout<Lecture>(
      ENDPOINTS.lectures.generateSummary(lectureId),
      undefined,
      { timeout: TIMEOUT_CONFIG.generation, onTimeout }
    )
  },

  /**
   * Clear the summary for a lecture (admin only).
   */
  clearSummary: (lectureId: number): Promise<Lecture> => {
    return httpClient.delete<Lecture>(ENDPOINTS.lectures.clearSummary(lectureId))
  },

  /**
   * Get recent lectures with audio, enriched with course/professor/topic data.
   * Used for homepage "Recently Added" section.
   *
   * @param limitOrIds - number for limit (default 4), or number[] for specific IDs
   */
  getRecentLectures: (limitOrIds: number | number[] = 4): Promise<RecentLecture[]> => {
    if (Array.isArray(limitOrIds)) {
      const ids = limitOrIds.join(',')
      return httpClient.get<RecentLecture[]>(`${ENDPOINTS.lectures.recent}?ids=${ids}`)
    }
    return httpClient.get<RecentLecture[]>(
      `${ENDPOINTS.lectures.recent}?limit=${String(limitOrIds)}`
    )
  },
}
