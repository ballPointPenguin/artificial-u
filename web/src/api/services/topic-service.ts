import { httpClient } from '../client.js'
import { ENDPOINTS, TIMEOUT_CONFIG } from '../config.js'
import type { Topic, TopicCreate, TopicList, TopicsGenerateRequest, TopicUpdate } from '../types.js'

export const topicService = {
  createTopic: (data: TopicCreate): Promise<Topic> => {
    return httpClient.post<Topic>(ENDPOINTS.topics.list, data)
  },

  getTopic: (topicId: number): Promise<Topic> => {
    return httpClient.get<Topic>(ENDPOINTS.topics.detail(topicId))
  },

  listTopicsByCourse: (courseId: number, page: number, size: number): Promise<TopicList> => {
    const params = new URLSearchParams({
      course_id: courseId.toString(),
      page: page.toString(),
      size: size.toString(),
    })
    return httpClient.get<TopicList>(`${ENDPOINTS.topics.list}?${params.toString()}`)
  },

  updateTopic: (topicId: number, data: TopicUpdate): Promise<Topic> => {
    return httpClient.patch<Topic>(ENDPOINTS.topics.detail(topicId), data)
  },
  deleteTopic: (topicId: number): Promise<undefined> => {
    return httpClient.delete(ENDPOINTS.topics.detail(topicId))
  },

  generateTopicsForCourse: (
    courseId: number,
    data?: TopicsGenerateRequest,
    onTimeout?: () => void
  ): Promise<Topic[]> => {
    let queryString = ''
    if (data?.freeform_prompt) {
      const queryParams = new URLSearchParams()
      queryParams.set('freeform_prompt', data.freeform_prompt)
      queryString = `?${queryParams.toString()}`
    }
    const requestBody =
      data && !data.freeform_prompt ? data : data?.freeform_prompt ? {} : undefined

    return httpClient.postWithExtendedTimeout<Topic[]>(
      `${ENDPOINTS.topics.generateForCourse(courseId)}${queryString}`,
      requestBody,
      { timeout: TIMEOUT_CONFIG.generation, onTimeout }
    )
  },

  enqueueGenerateTopicsForCourse: (
    courseId: number,
    data?: TopicsGenerateRequest
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    let queryString = ''
    if (data?.freeform_prompt) {
      const queryParams = new URLSearchParams()
      queryParams.set('freeform_prompt', data.freeform_prompt)
      queryString = `?${queryParams.toString()}`
    }
    const requestBody = undefined
    return httpClient.post(
      `${ENDPOINTS.topics.enqueueGenerateForCourse(courseId)}${queryString}`,
      requestBody
    )
  },

  // Batch generation methods (admin only)
  generateRemainingLectures: (
    topicId: number
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
    total_topics?: number
    message?: string
  }> => {
    return httpClient.post(ENDPOINTS.topics.generateRemainingLectures(topicId), undefined)
  },

  regenerateRemainingAudio: (
    topicId: number
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
    total_lectures?: number
    message?: string
  }> => {
    return httpClient.post(ENDPOINTS.topics.regenerateRemainingAudio(topicId), undefined)
  },

  regenerateRemainingLectures: (
    topicId: number
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
    total_topics?: number
    message?: string
  }> => {
    return httpClient.post(ENDPOINTS.topics.regenerateRemainingLectures(topicId), undefined)
  },
}
