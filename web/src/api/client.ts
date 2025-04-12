/**
 * API client with error handling
 */
import { API_CONFIG, DEFAULT_HEADERS } from './config'
import type { APIError } from './types'

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

    try {
      // Try to parse error response
      errorData = (await response.json()) as APIError
    } catch {
      // If parsing fails, use a generic error message
      errorData = {
        detail: response.statusText || 'An error occurred',
      }
    }

    throw new ApiError(
      errorData.detail || 'An unknown error occurred',
      response.status,
      errorData
    )
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
export async function fetchWithTimeout<T>(
  url: string,
  options: RequestOptions = {}
): Promise<T> {
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

    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown error',
      0
    )
  }
}

/**
 * HTTP client for API requests
 */
export const httpClient = {
  /**
   * Performs a GET request
   */
  get: async <T>(
    endpoint: string,
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
  post: async <T>(
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

    return fetchWithTimeout<T>(url, {
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
  put: async <T>(
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
  delete: async <T>(
    endpoint: string,
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

    return fetchWithTimeout<T>(url, {
      method: 'DELETE',
      headers,
      credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin',
      ...fetchOptions,
    })
  },
}
