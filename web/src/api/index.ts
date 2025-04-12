/**
 * API module
 *
 * Exports everything needed to interact with the backend API
 */

// Re-export everything from services
export * from './services'

// Re-export specific functions for convenience
export { getApiInfo, getHealthStatus } from './services/info-service'

// Export the API client and error handling
export { httpClient, ApiError } from './client'

// Export types
export * from './types'

// Export config
export { ENDPOINTS, API_CONFIG } from './config'
