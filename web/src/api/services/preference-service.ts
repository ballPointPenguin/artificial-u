/**
 * Preference service for global and user preferences
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'

export interface Preference {
  id: number
  student_id: number | null
  scope: string
  value: string
  is_global: boolean
}

export interface PreferenceValueUpdate {
  value: string
}

export interface LectureModelResponse {
  model: string
  source: 'preference' | 'environment'
}

export const preferenceService = {
  /**
   * List all global preferences (Admin only)
   */
  listGlobal: (): Promise<Preference[]> => {
    return httpClient.get<Preference[]>(ENDPOINTS.preferences.listGlobal)
  },

  /**
   * Get a specific global preference (Admin only)
   */
  getGlobal: (scope: string): Promise<Preference> => {
    return httpClient.get<Preference>(ENDPOINTS.preferences.getGlobal(scope))
  },

  /**
   * Set or update a global preference (Admin only)
   */
  setGlobal: (scope: string, value: string): Promise<Preference> => {
    return httpClient.put<Preference>(ENDPOINTS.preferences.setGlobal(scope), { value })
  },

  /**
   * Delete a global preference (Admin only)
   */
  deleteGlobal: async (scope: string): Promise<void> => {
    await httpClient.delete(ENDPOINTS.preferences.deleteGlobal(scope))
  },

  /**
   * Get the current lecture generation model
   */
  getLectureGenerationModel: (): Promise<LectureModelResponse> => {
    return httpClient.get<LectureModelResponse>(ENDPOINTS.preferences.lectureGenerationModel)
  },
}
