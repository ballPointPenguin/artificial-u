/**
 * Faculty service
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type { FacultiesListResponse } from '../types.js'

export const facultyService = {
  listFaculties: (): Promise<FacultiesListResponse> => {
    return httpClient.get<FacultiesListResponse>(ENDPOINTS.faculties.list)
  },
}
