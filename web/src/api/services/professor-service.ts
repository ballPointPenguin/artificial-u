/**
 * Professor service
 */
import { httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type {
  Professor,
  ProfessorCoursesResponse,
  ProfessorLecturesResponse,
  ProfessorsList,
} from '../types'

interface GetProfessorsParams {
  page?: number
  size?: number
  department?: string
  name?: string
  specialization?: string
}

/**
 * Get a paginated list of professors
 */
export async function getProfessors(
  params: GetProfessorsParams = {}
): Promise<ProfessorsList> {
  const queryParams = new URLSearchParams()

  if (params.page) queryParams.append('page', String(params.page))
  if (params.size) queryParams.append('size', String(params.size))
  if (params.department) queryParams.append('department', params.department)
  if (params.name) queryParams.append('name', params.name)
  if (params.specialization)
    queryParams.append('specialization', params.specialization)

  const queryString = queryParams.toString()
  const endpoint = `${ENDPOINTS.professors.list}${queryString ? `?${queryString}` : ''}`

  return httpClient.get<ProfessorsList>(endpoint)
}

/**
 * Get a professor by ID
 */
export async function getProfessor(id: number): Promise<Professor> {
  return httpClient.get<Professor>(ENDPOINTS.professors.detail(id))
}

/**
 * Get courses taught by a professor
 */
export async function getProfessorCourses(
  id: number
): Promise<ProfessorCoursesResponse> {
  return httpClient.get<ProfessorCoursesResponse>(
    ENDPOINTS.professors.courses(id)
  )
}

/**
 * Get lectures by a professor
 */
export async function getProfessorLectures(
  id: number
): Promise<ProfessorLecturesResponse> {
  return httpClient.get<ProfessorLecturesResponse>(
    ENDPOINTS.professors.lectures(id)
  )
}

/**
 * Create a new professor
 */
export async function createProfessor(
  data: Omit<Professor, 'id' | 'created_at' | 'updated_at'>
): Promise<Professor> {
  return httpClient.post<Professor>(ENDPOINTS.professors.list, data)
}

/**
 * Update a professor
 */
export async function updateProfessor(
  id: number,
  data: Partial<Omit<Professor, 'id' | 'created_at' | 'updated_at'>>
): Promise<Professor> {
  return httpClient.put<Professor>(ENDPOINTS.professors.detail(id), data)
}

/**
 * Delete a professor
 */
export async function deleteProfessor(
  id: number
): Promise<Record<string, never>> {
  return httpClient.delete<Record<string, never>>(
    ENDPOINTS.professors.detail(id)
  )
}

/**
 * Triggers the generation of a profile image for the specified professor.
 */
export async function generateProfessorImage(id: number): Promise<Professor> {
  return httpClient.post<Professor>(
    ENDPOINTS.professors.generateImage(id),
    {} // Empty body for this POST request
  )
}
