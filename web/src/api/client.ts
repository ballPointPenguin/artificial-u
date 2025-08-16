/**
 * API client with error handling
 */
import { API_CONFIG, DEFAULT_HEADERS } from './config'
import type { APIError } from './types'

// Optional token provider set by the app to attach Authorization headers
export let getAuthToken: null | (() => Promise<string | null>) = null
export const setTokenProvider = (fn: () => Promise<string | null>) => {
  getAuthToken = fn
}

async function attachAuthHeader(headers: Headers): Promise<void> {
  if (!getAuthToken) return
  try {
    const token = await getAuthToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  } catch {
    // ignore token retrieval errors; proceed without auth header
  }
}

export class ApiError extends Error {
  status: number
  data?: APIError

  constructor(message: string, status: number, data?: APIError) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export interface RequestOptions extends RequestInit {
  timeout?: number
  onTimeout?: () => void // Timeout callback
}

/**
 * Creates a complete URL by combining the base URL with the endpoint
 */
export const createUrl = (endpoint: string): string => {
  const baseUrl = API_CONFIG.baseUrl
  return `${baseUrl}${endpoint}`
}

/**
 * Handles API response and errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: APIError | undefined
    let errorMessage: string

    try {
      // Try to parse error response
      errorData = (await response.json()) as APIError
      // Check for the new error shape first, then fall back to the old one.
      errorMessage =
        errorData.message || errorData.detail || response.statusText || 'An unknown error occurred'
    } catch {
      // If parsing fails, use a generic error message
      errorMessage = response.statusText || 'An error occurred'
      errorData = { detail: errorMessage }
    }

    throw new ApiError(errorMessage, response.status, errorData)
  }

  // For successful responses
  if (response.status === 204) {
    // No content response
    return {} as T
  }

  return response.json() as Promise<T>
}

/**
 * Creates a timeout promise that rejects after specified milliseconds
 */
const timeout = (ms: number): Promise<never> => {
  return new Promise((_, reject) => {
    setTimeout(() => {
      reject(new ApiError('Request timeout', 408))
    }, ms)
  })
}

/**
 * Execute a fetch request with timeout and error handling
 */
export async function fetchWithTimeout<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const { timeout: timeoutMs = API_CONFIG.timeout, ...fetchOptions } = options

  try {
    const controller = new AbortController()
    const id = setTimeout(() => {
      controller.abort()
    }, timeoutMs)

    const response = await Promise.race([
      fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      }),
      timeout(timeoutMs),
    ])

    clearTimeout(id)
    return await handleResponse<T>(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('Request timed out', 408)
    }

    throw new ApiError(error instanceof Error ? error.message : 'Unknown error', 0)
  }
}

/**
 * Execute a fetch request with extended timeout support for long-running operations
 * For long-running requests like AI generation
 */
export async function fetchWithExtendedTimeout<T>(
  url: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeout: timeoutMs = API_CONFIG.timeout, onTimeout, ...fetchOptions } = options

  try {
    const controller = new AbortController()

    // Set up timeout with callback
    const timeoutId = setTimeout(() => {
      controller.abort()
      onTimeout?.()
    }, timeoutMs)

    const response = await Promise.race([
      fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      }),
      timeout(timeoutMs),
    ])

    clearTimeout(timeoutId)
    return await handleResponse<T>(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('Request timed out', 408)
    }

    throw new ApiError(error instanceof Error ? error.message : 'Unknown error', 0)
  }
}

/**
 * HTTP client for API requests
 */
export const httpClient = {
  /**
   * Performs a GET request
   */
  get: async <T>(endpoint: string, options: RequestOptions = {}): Promise<T> => {
    const url = createUrl(endpoint)
    const fetchOptions = { ...options }
    const headers = new Headers(DEFAULT_HEADERS)

    // Add headers from fetchOptions if present
    if (fetchOptions.headers) {
      const customHeaders = fetchOptions.headers
      if (customHeaders instanceof Headers) {
        for (const [key, value] of customHeaders.entries()) {
          headers.set(key, value)
        }
      } else if (typeof customHeaders === 'object') {
        for (const [key, value] of Object.entries(customHeaders)) {
          if (value) {
            headers.set(key, String(value))
          }
        }
      }
    }

    await attachAuthHeader(headers)
    return fetchWithTimeout<T>(url, {
      method: 'GET',
      headers,
      credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin',
      ...fetchOptions,
    })
  },

  /**
   * Performs a POST request
   */
  post: async <T>(endpoint: string, data: unknown, options: RequestOptions = {}): Promise<T> => {
    const url = createUrl(endpoint)
    const fetchOptions = { ...options }
    const headers = new Headers(DEFAULT_HEADERS)

    // Add headers from fetchOptions if present
    if (fetchOptions.headers) {
      const customHeaders = fetchOptions.headers
      if (customHeaders instanceof Headers) {
        for (const [key, value] of customHeaders.entries()) {
          headers.set(key, value)
        }
      } else if (typeof customHeaders === 'object') {
        for (const [key, value] of Object.entries(customHeaders)) {
          if (value) {
            headers.set(key, String(value))
          }
        }
      }
    }

    await attachAuthHeader(headers)
    return fetchWithTimeout<T>(url, {
      method: 'POST',
      headers,
      credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin',
      body: JSON.stringify(data),
      ...fetchOptions,
    })
  },

  /**
   * Performs a POST request with extended timeout for long-running operations
   */
  postWithExtendedTimeout: async <T>(
    endpoint: string,
    data: unknown,
    options: RequestOptions = {}
  ): Promise<T> => {
    const url = createUrl(endpoint)
    const fetchOptions = { ...options }
    const headers = new Headers(DEFAULT_HEADERS)

    // Add headers from fetchOptions if present
    if (fetchOptions.headers) {
      const customHeaders = fetchOptions.headers
      if (customHeaders instanceof Headers) {
        for (const [key, value] of customHeaders.entries()) {
          headers.set(key, value)
        }
      } else if (typeof customHeaders === 'object') {
        for (const [key, value] of Object.entries(customHeaders)) {
          if (value) {
            headers.set(key, String(value))
          }
        }
      }
    }

    await attachAuthHeader(headers)
    return fetchWithExtendedTimeout<T>(url, {
      method: 'POST',
      headers,
      credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin',
      body: JSON.stringify(data),
      ...fetchOptions,
    })
  },

  /**
   * Performs a PUT request
   */
  put: async <T>(endpoint: string, data: unknown, options: RequestOptions = {}): Promise<T> => {
    const url = createUrl(endpoint)
    const fetchOptions = { ...options }
    const headers = new Headers(DEFAULT_HEADERS)

    // Add headers from fetchOptions if present
    if (fetchOptions.headers) {
      const customHeaders = fetchOptions.headers
      if (customHeaders instanceof Headers) {
        for (const [key, value] of customHeaders.entries()) {
          headers.set(key, value)
        }
      } else if (typeof customHeaders === 'object') {
        for (const [key, value] of Object.entries(customHeaders)) {
          if (value) {
            headers.set(key, String(value))
          }
        }
      }
    }

    await attachAuthHeader(headers)
    return fetchWithTimeout<T>(url, {
      method: 'PUT',
      headers,
      credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin',
      body: JSON.stringify(data),
      ...fetchOptions,
    })
  },

  /**
   * Performs a DELETE request
   */
  delete: async <T>(endpoint: string, options: RequestOptions = {}): Promise<T> => {
    const url = createUrl(endpoint)
    const fetchOptions = { ...options }
    const headers = new Headers(DEFAULT_HEADERS)

    // Add headers from fetchOptions if present
    if (fetchOptions.headers) {
      const customHeaders = fetchOptions.headers
      if (customHeaders instanceof Headers) {
        for (const [key, value] of customHeaders.entries()) {
          headers.set(key, value)
        }
      } else if (typeof customHeaders === 'object') {
        for (const [key, value] of Object.entries(customHeaders)) {
          if (value) {
            headers.set(key, String(value))
          }
        }
      }
    }

    await attachAuthHeader(headers)
    return fetchWithTimeout<T>(url, {
      method: 'DELETE',
      headers,
      credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin',
      ...fetchOptions,
    })
  },

  /**
   * Performs a PATCH request
   */
  patch: async <T>(endpoint: string, data: unknown, options: RequestOptions = {}): Promise<T> => {
    const url = createUrl(endpoint)
    const fetchOptions = { ...options }
    const headers = new Headers(DEFAULT_HEADERS)

    // Add headers from fetchOptions if present
    if (fetchOptions.headers) {
      const customHeaders = fetchOptions.headers
      if (customHeaders instanceof Headers) {
        for (const [key, value] of customHeaders.entries()) {
          headers.set(key, value)
        }
      } else if (typeof customHeaders === 'object') {
        for (const [key, value] of Object.entries(customHeaders)) {
          if (value) {
            headers.set(key, String(value))
          }
        }
      }
    }

    await attachAuthHeader(headers)
    return fetchWithTimeout<T>(url, {
      method: 'PATCH',
      headers,
      credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin',
      body: JSON.stringify(data),
      ...fetchOptions,
    })
  },
}
