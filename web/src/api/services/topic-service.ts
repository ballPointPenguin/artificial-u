import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type { Topic, TopicCreate, TopicList, TopicUpdate, TopicsGenerateRequest } from '../types.js'

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

  generateTopicsForCourse: (courseId: number, data?: TopicsGenerateRequest): Promise<Topic[]> => {
    let queryString = ''
    if (data?.freeform_prompt) {
      const queryParams = new URLSearchParams()
      queryParams.set('freeform_prompt', data.freeform_prompt)
      queryString = `?${queryParams.toString()}`
    }
    const requestBody =
      data && !data.freeform_prompt ? data : data?.freeform_prompt ? {} : undefined

    return httpClient.post<Topic[]>(
      `${ENDPOINTS.topics.generateForCourse(courseId)}${queryString}`,
      requestBody
    )
  },
}
