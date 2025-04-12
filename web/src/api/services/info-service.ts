/**
 * API Info service
 */
import { httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type { APIInfo, HealthCheckResponse } from '../types'

/**
 * Get basic API information
 */
export async function getApiInfo(): Promise<APIInfo> {
  return httpClient.get<APIInfo>(ENDPOINTS.info)
}

/**
 * Get API health status
 */
export async function getHealthStatus(): Promise<HealthCheckResponse> {
  return httpClient.get<HealthCheckResponse>(ENDPOINTS.health)
}
