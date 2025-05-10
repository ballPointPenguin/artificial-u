/**
 * Professor service
 */
import { httpClient } from '../client'
import type {
  Professor,
  ProfessorCoursesResponse,
  ProfessorCreate,
  ProfessorGenerateRequest,
  ProfessorLecturesResponse,
  ProfessorUpdate,
  ProfessorsListResponse,
} from '../types'

const PROFESSORS_ENDPOINT = '/professors'

interface ListProfessorsParams {
  page: number
  size: number
  departmentId?: number
  name?: string
  specialization?: string
}

export const professorService = {
  listProfessors: (params: ListProfessorsParams): Promise<ProfessorsListResponse> => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      size: params.size.toString(),
    })
    if (params.departmentId) queryParams.set('department_id', params.departmentId.toString())
    if (params.name) queryParams.set('name', params.name)
    if (params.specialization) queryParams.set('specialization', params.specialization)
    return httpClient.get<ProfessorsListResponse>(`${PROFESSORS_ENDPOINT}?${queryParams.toString()}`)
  },

  getProfessor: (professorId: number): Promise<Professor> => {
    return httpClient.get<Professor>(`${PROFESSORS_ENDPOINT}/${professorId}`)
  },

  createProfessor: (data: ProfessorCreate): Promise<Professor> => {
    return httpClient.post<Professor>(PROFESSORS_ENDPOINT, data)
  },

  updateProfessor: (professorId: number, data: ProfessorUpdate): Promise<Professor> => {
    return httpClient.put<Professor>(`${PROFESSORS_ENDPOINT}/${professorId}`, data)
  },

  deleteProfessor: (professorId: number): Promise<void> => {
    return httpClient.delete<void>(`${PROFESSORS_ENDPOINT}/${professorId}`)
  },

  getProfessorCourses: (professorId: number): Promise<ProfessorCoursesResponse> => {
    return httpClient.get<ProfessorCoursesResponse>(`${PROFESSORS_ENDPOINT}/${professorId}/courses`)
  },

  getProfessorLectures: (professorId: number): Promise<ProfessorLecturesResponse> => {
    return httpClient.get<ProfessorLecturesResponse>(`${PROFESSORS_ENDPOINT}/${professorId}/lectures`)
  },

  generateProfessorImage: (professorId: number): Promise<Professor> => {
    return httpClient.post<Professor>(`${PROFESSORS_ENDPOINT}/${professorId}/generate-image`, {})
  },

  generateProfessor: (data: ProfessorGenerateRequest): Promise<Professor> => {
    return httpClient.post<Professor>(`${PROFESSORS_ENDPOINT}/generate`, data)
  },
}
