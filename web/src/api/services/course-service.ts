/**
 * Course service
 */
import { httpClient } from '../client'
import type {
  Course,
  CourseCreate,
  CourseGenerateRequest,
  CourseLecturesResponse,
  CourseUpdate,
  CoursesListResponse,
  DepartmentBrief,
  ProfessorBrief,
} from '../types'

const COURSES_ENDPOINT = '/courses'

interface ListCoursesParams {
  page: number
  size: number
  departmentId?: number
  professorId?: number
  level?: string
  title?: string
}

export const courseService = {
  listCourses: (params: ListCoursesParams): Promise<CoursesListResponse> => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      size: params.size.toString(),
    })
    if (params.departmentId) queryParams.set('department_id', params.departmentId.toString())
    if (params.professorId) queryParams.set('professor_id', params.professorId.toString())
    if (params.level) queryParams.set('level', params.level)
    if (params.title) queryParams.set('title', params.title)
    return httpClient.get<CoursesListResponse>(`${COURSES_ENDPOINT}?${queryParams.toString()}`)
  },

  getCourse: (courseId: number): Promise<Course> => {
    return httpClient.get<Course>(`${COURSES_ENDPOINT}/${courseId}`)
  },

  getCourseByCode: (code: string): Promise<Course> => {
    return httpClient.get<Course>(`${COURSES_ENDPOINT}/code/${code}`)
  },

  createCourse: (data: CourseCreate): Promise<Course> => {
    return httpClient.post<Course>(COURSES_ENDPOINT, data)
  },

  updateCourse: (courseId: number, data: CourseUpdate): Promise<Course> => {
    return httpClient.put<Course>(`${COURSES_ENDPOINT}/${courseId}`, data) // Python uses PUT
  },

  deleteCourse: (courseId: number): Promise<void> => {
    return httpClient.delete<void>(`${COURSES_ENDPOINT}/${courseId}`)
  },

  getCourseProfessor: (courseId: number): Promise<ProfessorBrief> => {
    return httpClient.get<ProfessorBrief>(`${COURSES_ENDPOINT}/${courseId}/professor`)
  },

  getCourseDepartment: (courseId: number): Promise<DepartmentBrief> => {
    return httpClient.get<DepartmentBrief>(`${COURSES_ENDPOINT}/${courseId}/department`)
  },

  getCourseLectures: (courseId: number): Promise<CourseLecturesResponse> => {
    return httpClient.get<CourseLecturesResponse>(`${COURSES_ENDPOINT}/${courseId}/lectures`)
  },

  generateCourse: (data: CourseGenerateRequest): Promise<Course> => {
    return httpClient.post<Course>(`${COURSES_ENDPOINT}/generate`, data)
  },
}
