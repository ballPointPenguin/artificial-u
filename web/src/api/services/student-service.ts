/**
 * Student service for profile operations
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type { Student, StudentUpdate } from '../types.js'

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
}
