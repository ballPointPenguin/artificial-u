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
}
