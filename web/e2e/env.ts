/** Where the tests point. The API is same-origin in production and on :8000 locally. */
export const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:5173'

const isLocal = /^https?:\/\/(localhost|127\.0\.0\.1)/.test(baseURL)

export const apiURL =
  process.env.E2E_API_URL ?? (isLocal ? 'http://localhost:8000/api' : `${baseURL}/api`)
