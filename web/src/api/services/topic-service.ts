import { httpClient } from '../client'
import type { Topic, TopicCreate, TopicList, TopicUpdate } from '../types'

const TOPICS_ENDPOINT = '/topics'
const COURSES_ENDPOINT = '/courses'

export const topicService = {
  createTopic: (data: TopicCreate): Promise<Topic> => {
    return httpClient.post<Topic>(TOPICS_ENDPOINT, data)
  },

  getTopic: (topicId: number): Promise<Topic> => {
    return httpClient.get<Topic>(`${TOPICS_ENDPOINT}/${topicId}`)
  },

  listTopicsByCourse: (
    courseId: number,
    page: number,
    size: number
  ): Promise<TopicList> => {
    const params = new URLSearchParams({
      course_id: courseId.toString(),
      page: page.toString(),
      size: size.toString(),
    })
    return httpClient.get<TopicList>(`${TOPICS_ENDPOINT}?${params.toString()}`)
  },

  updateTopic: (topicId: number, data: TopicUpdate): Promise<Topic> => {
    return httpClient.patch<Topic>(`${TOPICS_ENDPOINT}/${topicId}`, data) // Assuming PATCH, will verify Python router
  },

  deleteTopic: (topicId: number): Promise<void> => {
    return httpClient.delete<void>(`${TOPICS_ENDPOINT}/${topicId}`)
  },

  generateTopicsForCourse: (
    courseId: number,
    freeformPrompt?: string
  ): Promise<Topic[]> => {
    const params = new URLSearchParams()
    if (freeformPrompt) {
      params.set('freeform_prompt', freeformPrompt)
    }
    const queryString = params.toString() ? `?${params.toString()}` : ''
    return httpClient.post<Topic[]>(
      `${COURSES_ENDPOINT}/${courseId}/topics/generate${queryString}`,
      {} // Empty body as prompt is a query param
    )
  },
}