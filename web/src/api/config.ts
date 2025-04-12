/**
 * API configuration
 */

// Environment-specific base URLs
const API_BASE_URLS = {
  development: 'http://localhost:8000/api',
  test: 'http://localhost:8000/api',
  production: '/api', // Relative path for same-domain production deployment
}

// Determine current environment
const getEnvironment = (): 'development' | 'test' | 'production' => {
  if (import.meta.env.MODE === 'test') return 'test'
  if (import.meta.env.PROD) return 'production'
  return 'development'
}

// Config for the current environment
export const API_CONFIG = {
  baseUrl: API_BASE_URLS[getEnvironment()],
  timeout: 30000, // 30 seconds
  withCredentials: false,
}

// Default headers for all API requests
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  Accept: 'application/json',
}

// Endpoints
export const ENDPOINTS = {
  info: '/',
  health: '/v1/health',
  professors: {
    list: '/v1/professors',
    detail: (id: number) => `/v1/professors/${String(id)}`,
    courses: (id: number) => `/v1/professors/${String(id)}/courses`,
    lectures: (id: number) => `/v1/professors/${String(id)}/lectures`,
  },
  departments: {
    list: '/v1/departments',
    detail: (id: number) => `/v1/departments/${String(id)}`,
  },
  courses: {
    list: '/v1/courses',
    detail: (id: number) => `/v1/courses/${String(id)}`,
    lectures: (id: number) => `/v1/courses/${String(id)}/lectures`,
  },
  lectures: {
    list: '/v1/lectures',
    detail: (id: number) => `/v1/lectures/${String(id)}`,
  },
}
