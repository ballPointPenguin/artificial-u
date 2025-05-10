/**
 * Professor service
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type {
  Professor,
  ProfessorCoursesResponse,
  ProfessorCreate,
  ProfessorGenerateRequest,
  ProfessorLecturesResponse,
  ProfessorUpdate,
  ProfessorsListResponse,
} from '../types.js'

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
    return httpClient.get<ProfessorsListResponse>(
      `${ENDPOINTS.professors.list}?${queryParams.toString()}`
    )
  },

  getProfessor: (professorId: number): Promise<Professor> => {
    return httpClient.get<Professor>(ENDPOINTS.professors.detail(professorId))
  },

  createProfessor: (data: ProfessorCreate): Promise<Professor> => {
    return httpClient.post<Professor>(ENDPOINTS.professors.list, data)
  },

  updateProfessor: (professorId: number, data: ProfessorUpdate): Promise<Professor> => {
    return httpClient.put<Professor>(ENDPOINTS.professors.detail(professorId), data)
  },
  deleteProfessor: (professorId: number): Promise<undefined> => {
    return httpClient.delete(ENDPOINTS.professors.detail(professorId))
  },

  getProfessorCourses: (professorId: number): Promise<ProfessorCoursesResponse> => {
    return httpClient.get<ProfessorCoursesResponse>(ENDPOINTS.professors.courses(professorId))
  },

  getProfessorLectures: (professorId: number): Promise<ProfessorLecturesResponse> => {
    return httpClient.get<ProfessorLecturesResponse>(ENDPOINTS.professors.lectures(professorId))
  },

  generateProfessorImage: (professorId: number): Promise<Professor> => {
    return httpClient.post<Professor>(ENDPOINTS.professors.generateImage(professorId), {})
  },

  generateProfessor: (data: ProfessorGenerateRequest): Promise<Professor> => {
    return httpClient.post<Professor>(ENDPOINTS.professors.generate, data)
  },
}
