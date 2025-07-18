/**
 * API module
 *
 * Exports everything needed to interact with the backend API
 */

// Export the API client and error handling
export { ApiError, httpClient } from './client'
// Export config
export { API_CONFIG, ENDPOINTS } from './config'
// Re-export everything from services
export * from './services'
// Re-export specific functions for convenience
export { getApiInfo, getHealthStatus } from './services/info-service'
// Export types
export * from './types'
