/**
 * Department service
 */
import { httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type { Department, DepartmentsList } from '../types'

interface GetDepartmentsParams {
  page?: number
  size?: number
  name?: string
}

/**
 * Get a paginated list of departments
 */
export async function getDepartments(
  params: GetDepartmentsParams = {}
): Promise<DepartmentsList> {
  const queryParams = new URLSearchParams()

  if (params.page) queryParams.append('page', String(params.page))
  if (params.size) queryParams.append('size', String(params.size))
  if (params.name) queryParams.append('name', params.name)

  const queryString = queryParams.toString()
  const endpoint = `${ENDPOINTS.departments.list}${queryString ? `?${queryString}` : ''}`

  return httpClient.get<DepartmentsList>(endpoint)
}

/**
 * Get a department by ID
 */
export async function getDepartment(id: number): Promise<Department> {
  return httpClient.get<Department>(ENDPOINTS.departments.detail(id))
}

/**
 * Create a new department
 */
export async function createDepartment(
  data: Omit<Department, 'id' | 'created_at' | 'updated_at'>
): Promise<Department> {
  return httpClient.post<Department>(ENDPOINTS.departments.list, data)
}

/**
 * Update a department
 */
export async function updateDepartment(
  id: number,
  data: Partial<Omit<Department, 'id' | 'created_at' | 'updated_at'>>
): Promise<Department> {
  return httpClient.put<Department>(ENDPOINTS.departments.detail(id), data)
}

/**
 * Delete a department
 */
export async function deleteDepartment(
  id: number
): Promise<Record<string, never>> {
  return httpClient.delete<Record<string, never>>(
    ENDPOINTS.departments.detail(id)
  )
}
