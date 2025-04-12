/**
 * Course service
 */
import { httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type { Course, CoursesList, LecturesList } from '../types'

interface GetCoursesParams {
  page?: number
  size?: number
  department?: string
  professor_id?: number
  semester?: string
  title?: string
}

/**
 * Get a paginated list of courses
 */
export async function getCourses(
  params: GetCoursesParams = {}
): Promise<CoursesList> {
  const queryParams = new URLSearchParams()

  if (params.page) queryParams.append('page', String(params.page))
  if (params.size) queryParams.append('size', String(params.size))
  if (params.department) queryParams.append('department', params.department)
  if (params.professor_id)
    queryParams.append('professor_id', String(params.professor_id))
  if (params.semester) queryParams.append('semester', params.semester)
  if (params.title) queryParams.append('title', params.title)

  const queryString = queryParams.toString()
  const endpoint = `${ENDPOINTS.courses.list}${queryString ? `?${queryString}` : ''}`

  return httpClient.get<CoursesList>(endpoint)
}

/**
 * Get a course by ID
 */
export async function getCourse(id: number): Promise<Course> {
  return httpClient.get<Course>(ENDPOINTS.courses.detail(id))
}

/**
 * Get lectures for a course
 */
export async function getCourseLectures(id: number): Promise<LecturesList> {
  return httpClient.get<LecturesList>(ENDPOINTS.courses.lectures(id))
}

/**
 * Create a new course
 */
export async function createCourse(
  data: Omit<Course, 'id' | 'created_at' | 'updated_at'>
): Promise<Course> {
  return httpClient.post<Course>(ENDPOINTS.courses.list, data)
}

/**
 * Update a course
 */
export async function updateCourse(
  id: number,
  data: Partial<Omit<Course, 'id' | 'created_at' | 'updated_at'>>
): Promise<Course> {
  return httpClient.put<Course>(ENDPOINTS.courses.detail(id), data)
}

/**
 * Delete a course
 */
export async function deleteCourse(id: number): Promise<Record<string, never>> {
  return httpClient.delete<Record<string, never>>(ENDPOINTS.courses.detail(id))
}
