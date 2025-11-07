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
  ProfessorsListResponse,
  ProfessorUpdate,
} from '../types.js'

interface ListProfessorsParams {
  page: number
  size: number
  departmentId?: number
  facultyId?: number
  name?: string
  specialization?: string
}

export const professorService = {
  listProfessors: (params: ListProfessorsParams): Promise<ProfessorsListResponse> => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      size: params.size.toString(),
    })
    if (params.facultyId) queryParams.set('faculty_id', params.facultyId.toString())
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

  enqueueGenerateProfessor: (
    data: ProfessorGenerateRequest
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.professors.enqueueGenerate, data)
  },

  enqueueGenerateProfessorImage: (
    professorId: number
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.professors.enqueueGenerateImage(professorId), {})
  },

  assignVoiceToProfessor: (professorId: number): Promise<Professor> => {
    return httpClient.post<Professor>(ENDPOINTS.professors.assignVoice(professorId), {})
  },
}
