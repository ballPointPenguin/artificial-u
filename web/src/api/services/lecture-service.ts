/**
 * Lecture service
 */
import { createUrl, httpClient } from '../client'
import { ENDPOINTS, TIMEOUT_CONFIG } from '../config'
import type {
  AudioRedirectResponse,
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

  /**
   * Trigger generation of lecture audio. No body required.
   * Uses extended timeout similar to other generation actions.
   */
  generateLectureAudio: (lectureId: number, onTimeout?: () => void): Promise<Lecture> => {
    return httpClient.postWithExtendedTimeout<Lecture>(
      ENDPOINTS.lectures.generateAudio(lectureId),
      undefined,
      { timeout: TIMEOUT_CONFIG.generation, onTimeout }
    )
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

  /**
   * Generate lecture with extended timeout for long-running operations
   */
  generateLecture: (data: LectureGenerateRequest, onTimeout?: () => void): Promise<Lecture> => {
    return httpClient.postWithExtendedTimeout<Lecture>(ENDPOINTS.lectures.generate, data, {
      timeout: TIMEOUT_CONFIG.generation,
      onTimeout,
    })
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
   * Generate lecture text only with extended timeout for long-running operations.
   * This generates only the lecture text content without automatically triggering
   * audio or summary generation.
   */
  generateLectureTextOnly: (
    data: LectureGenerateRequest,
    onTimeout?: () => void
  ): Promise<Lecture> => {
    return httpClient.postWithExtendedTimeout<Lecture>(ENDPOINTS.lectures.generateTextOnly, data, {
      timeout: TIMEOUT_CONFIG.generation,
      onTimeout,
    })
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
