/**
 * Department service
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type {
  Department,
  DepartmentCoursesResponse,
  DepartmentCreate,
  DepartmentGenerateRequest,
  DepartmentProfessorsResponse,
  DepartmentsListResponse,
  DepartmentUpdate,
} from '../types.js'

interface ListDepartmentsParams {
  page: number
  size: number
  faculty_id?: number
  name?: string
  language?: string
}

export const departmentService = {
  listDepartments: (params: ListDepartmentsParams): Promise<DepartmentsListResponse> => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      size: params.size.toString(),
    })
    if (params.faculty_id) queryParams.set('faculty_id', params.faculty_id.toString())
    if (params.name) queryParams.set('name', params.name)
    if (params.language) queryParams.set('language', params.language)
    return httpClient.get<DepartmentsListResponse>(
      `${ENDPOINTS.departments.list}?${queryParams.toString()}`
    )
  },

  getDepartment: (departmentId: number): Promise<Department> => {
    return httpClient.get<Department>(ENDPOINTS.departments.detail(departmentId))
  },

  getDepartmentByCode: (code: string): Promise<Department> => {
    return httpClient.get<Department>(ENDPOINTS.departments.code(code))
  },

  createDepartment: (data: DepartmentCreate): Promise<Department> => {
    return httpClient.post<Department>(ENDPOINTS.departments.list, data)
  },

  updateDepartment: (departmentId: number, data: DepartmentUpdate): Promise<Department> => {
    return httpClient.put<Department>(ENDPOINTS.departments.detail(departmentId), data)
  },
  deleteDepartment: (departmentId: number): Promise<null> => {
    return httpClient.delete<null>(ENDPOINTS.departments.detail(departmentId))
  },

  getDepartmentProfessors: (departmentId: number): Promise<DepartmentProfessorsResponse> => {
    return httpClient.get<DepartmentProfessorsResponse>(
      ENDPOINTS.departments.professors(departmentId)
    )
  },

  getDepartmentCourses: (departmentId: number): Promise<DepartmentCoursesResponse> => {
    return httpClient.get<DepartmentCoursesResponse>(ENDPOINTS.departments.courses(departmentId))
  },

  generateDepartment: (data: DepartmentGenerateRequest): Promise<Department> => {
    return httpClient.post<Department>(ENDPOINTS.departments.generate, data)
  },

  enqueueGenerateDepartment: (
    data: DepartmentGenerateRequest
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.departments.enqueueGenerate, data)
  },
}
