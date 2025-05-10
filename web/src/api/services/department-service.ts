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
  DepartmentUpdate,
  DepartmentsListResponse,
} from '../types.js'

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
}
