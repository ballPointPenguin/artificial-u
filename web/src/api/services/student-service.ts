/**
 * Student service for profile operations
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type { PaginatedResponse, Student, StudentUpdate } from '../types.js'

interface ListStudentsParams {
  page?: number
  size?: number
  name?: string
  email?: string
  role?: 'viewer' | 'creator' | 'admin'
}

export const studentService = {
  /**
   * Get current student profile
   */
  getCurrentStudent: (): Promise<Student> => {
    return httpClient.get<Student>(ENDPOINTS.students.me)
  },

  /**
   * Update current student profile
   */
  updateCurrentStudent: (data: StudentUpdate): Promise<Student> => {
    return httpClient.patch<Student>(ENDPOINTS.students.me, data)
  },

  /**
   * List all students (Admin only)
   */
  listStudents: (params?: ListStudentsParams): Promise<PaginatedResponse<Student>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.set('page', String(params.page))
    if (params?.size) queryParams.set('size', String(params.size))
    if (params?.name) queryParams.set('name', params.name)
    if (params?.email) queryParams.set('email', params.email)
    if (params?.role) queryParams.set('role', params.role)

    const queryString = queryParams.toString()
    const url = queryString ? `${ENDPOINTS.students.list}?${queryString}` : ENDPOINTS.students.list

    return httpClient.get<PaginatedResponse<Student>>(url)
  },

  /**
   * Update student role (Admin only)
   */
  updateStudentRole: (id: number, role: 'viewer' | 'creator' | 'admin'): Promise<Student> => {
    return httpClient.patch<Student>(ENDPOINTS.students.updateRole(id), {
      role,
    })
  },

  /**
   * Add coins to student account (Admin only)
   */
  addStudentCoins: (id: number, amount: number): Promise<Student> => {
    return httpClient.post<Student>(ENDPOINTS.students.addCoins(id), { amount })
  },

  /**
   * Delete a student (Admin only)
   */
  deleteStudent: async (id: number): Promise<void> => {
    await httpClient.delete(ENDPOINTS.students.detail(id))
  },
}
