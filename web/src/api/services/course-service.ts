/**
 * Course service
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type {
  Course,
  CourseCreate,
  CourseGenerateRequest,
  CourseLecturesResponse,
  CourseUpdate,
  CoursesListResponse,
  DepartmentBrief,
  ProfessorBrief,
} from '../types.js'

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
    return httpClient.get<CoursesListResponse>(
      `${ENDPOINTS.courses.list}?${queryParams.toString()}`
    )
  },

  getCourse: (courseId: number): Promise<Course> => {
    return httpClient.get<Course>(ENDPOINTS.courses.detail(courseId))
  },

  getCourseByCode: (code: string): Promise<Course> => {
    return httpClient.get<Course>(ENDPOINTS.courses.code(code))
  },

  createCourse: (data: CourseCreate): Promise<Course> => {
    return httpClient.post<Course>(ENDPOINTS.courses.list, data)
  },

  updateCourse: (courseId: number, data: CourseUpdate): Promise<Course> => {
    return httpClient.put<Course>(ENDPOINTS.courses.detail(courseId), data)
  },
  deleteCourse: (courseId: number): Promise<undefined> => {
    return httpClient.delete(ENDPOINTS.courses.detail(courseId))
  },

  getCourseProfessor: (courseId: number): Promise<ProfessorBrief> => {
    return httpClient.get<ProfessorBrief>(ENDPOINTS.courses.professor(courseId))
  },

  getCourseDepartment: (courseId: number): Promise<DepartmentBrief> => {
    return httpClient.get<DepartmentBrief>(ENDPOINTS.courses.department(courseId))
  },

  getCourseLectures: (courseId: number): Promise<CourseLecturesResponse> => {
    return httpClient.get<CourseLecturesResponse>(ENDPOINTS.courses.lectures(courseId))
  },

  generateCourse: (data: CourseGenerateRequest): Promise<Course> => {
    return httpClient.post<Course>(ENDPOINTS.courses.generate, data)
  },
}
