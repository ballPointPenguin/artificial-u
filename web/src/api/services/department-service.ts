/**
 * Department service
 */
import { httpClient } from '../client'
import type {
  Department,
  DepartmentCoursesResponse,
  DepartmentCreate,
  DepartmentGenerateRequest,
  DepartmentProfessorsResponse,
  DepartmentUpdate,
  DepartmentsListResponse,
} from '../types'

const DEPARTMENTS_ENDPOINT = '/departments'

interface ListDepartmentsParams {
  page: number
  size: number
  faculty?: string
  name?: string
}

export const departmentService = {
  listDepartments: (params: ListDepartmentsParams): Promise<DepartmentsListResponse> => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      size: params.size.toString(),
    })
    if (params.faculty) queryParams.set('faculty', params.faculty)
    if (params.name) queryParams.set('name', params.name)
    return httpClient.get<DepartmentsListResponse>(`${DEPARTMENTS_ENDPOINT}?${queryParams.toString()}`)
  },

  getDepartment: (departmentId: number): Promise<Department> => {
    return httpClient.get<Department>(`${DEPARTMENTS_ENDPOINT}/${departmentId}`)
  },

  getDepartmentByCode: (code: string): Promise<Department> => {
    return httpClient.get<Department>(`${DEPARTMENTS_ENDPOINT}/code/${code}`)
  },

  createDepartment: (data: DepartmentCreate): Promise<Department> => {
    return httpClient.post<Department>(DEPARTMENTS_ENDPOINT, data)
  },

  updateDepartment: (departmentId: number, data: DepartmentUpdate): Promise<Department> => {
    return httpClient.put<Department>(`${DEPARTMENTS_ENDPOINT}/${departmentId}`, data)
  },

  deleteDepartment: (departmentId: number): Promise<void> => {
    return httpClient.delete<void>(`${DEPARTMENTS_ENDPOINT}/${departmentId}`)
  },

  getDepartmentProfessors: (departmentId: number): Promise<DepartmentProfessorsResponse> => {
    return httpClient.get<DepartmentProfessorsResponse>(`${DEPARTMENTS_ENDPOINT}/${departmentId}/professors`)
  },

  getDepartmentCourses: (departmentId: number): Promise<DepartmentCoursesResponse> => {
    return httpClient.get<DepartmentCoursesResponse>(`${DEPARTMENTS_ENDPOINT}/${departmentId}/courses`)
  },

  generateDepartment: (data: DepartmentGenerateRequest): Promise<Department> => {
    return httpClient.post<Department>(`${DEPARTMENTS_ENDPOINT}/generate`, data)
  },
}
