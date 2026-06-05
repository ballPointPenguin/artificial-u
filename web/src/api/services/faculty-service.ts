/**
 * Faculty service
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type { FacultiesListResponse } from '../types.js'

export interface ListFacultiesParams {
  language?: string
}

export const facultyService = {
  listFaculties: (params?: ListFacultiesParams): Promise<FacultiesListResponse> => {
    const url = new URL(ENDPOINTS.faculties.list, window.location.origin)
    if (params?.language) url.searchParams.set('language', params.language)
    return httpClient.get<FacultiesListResponse>(url.pathname + url.search)
  },
}
