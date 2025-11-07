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

// Timeout configurations for different request types
export const TIMEOUT_CONFIG = {
  default: 30000, // 30 seconds
  generation: 300000, // 5 minutes for AI generation
  upload: 120000, // 2 minutes for file uploads
  download: 60000, // 1 minute for downloads
}

// Default headers for all API requests
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  Accept: 'application/json',
}

// Endpoints
export const ENDPOINTS = {
  info: '/v1/info',
  health: '/v1/health',
  professors: {
    list: '/v1/professors',
    detail: (id: number) => `/v1/professors/${String(id)}`,
    courses: (id: number) => `/v1/professors/${String(id)}/courses`,
    lectures: (id: number) => `/v1/professors/${String(id)}/lectures`,
    generateImage: (id: number) => `/v1/professors/${String(id)}/generate-image`,
    enqueueGenerateImage: (id: number) => `/v1/professors/${String(id)}/generate-image/enqueue`,
    generate: '/v1/professors/generate',
    enqueueGenerate: '/v1/professors/generate/enqueue',
    assignVoice: (id: number) => `/v1/professors/${String(id)}/assign-voice`,
  },
  departments: {
    list: '/v1/departments',
    detail: (id: number) => `/v1/departments/${String(id)}`,
    generate: '/v1/departments/generate',
    enqueueGenerate: '/v1/departments/generate/enqueue',
    code: (code: string | number) => `/v1/departments/code/${String(code)}`,
    professors: (id: number) => `/v1/departments/${String(id)}/professors`,
    courses: (id: number) => `/v1/departments/${String(id)}/courses`,
  },
  faculties: {
    list: '/v1/faculties',
  },
  courses: {
    list: '/v1/courses',
    detail: (id: number) => `/v1/courses/${String(id)}`,
    lectures: (id: number) => `/v1/courses/${String(id)}/lectures`,
    professor: (id: number) => `/v1/courses/${String(id)}/professor`,
    department: (id: number) => `/v1/courses/${String(id)}/department`,
    code: (code: string | number) => `/v1/courses/code/${String(code)}`,
    generate: '/v1/courses/generate',
    enqueueGenerate: '/v1/courses/generate/enqueue',
    enqueueCreate: '/v1/courses/create/enqueue',
  },
  jobs: {
    list: '/v1/jobs',
    detail: (id: number) => `/v1/jobs/${String(id)}`,
    summary: '/v1/jobs/summary',
    stream: '/v1/jobs/stream',
  },
  lectures: {
    list: '/v1/lectures',
    detail: (id: number) => `/v1/lectures/${String(id)}`,
    generate: '/v1/lectures/generate',
    enqueueGenerate: '/v1/lectures/generate/enqueue',
    content: (id: number) => `/v1/lectures/${String(id)}/content`,
    audio: (id: number) => `/v1/lectures/${String(id)}/audio`,
    generateAudio: (id: number) => `/v1/lectures/${String(id)}/generate-audio`,
    enqueueGenerateAudio: (id: number) => `/v1/lectures/${String(id)}/generate-audio/enqueue`,
    download: (id: number) => `/v1/lectures/${String(id)}/content/download`,
  },
  topics: {
    list: '/v1/topics',
    detail: (id: number) => `/v1/topics/${String(id)}`,
    generateForCourse: (courseId: number) => `/v1/courses/${String(courseId)}/topics/generate`,
    enqueueGenerateForCourse: (courseId: number) =>
      `/v1/courses/${String(courseId)}/topics/generate/enqueue`,
  },
  voices: {
    manualAssignVoice: (professorId: string) => `/v1/voices/${professorId}/assign_voice`,
    listVoices: '/v1/voices/',
    getVoice: (voiceId: number) => `/v1/voices/${String(voiceId)}`,
    getVoiceByElId: (elVoiceId: string) => `/v1/voices/by_el/${encodeURIComponent(elVoiceId)}`,
  },
  students: {
    me: '/v1/students/me',
    list: '/v1/students',
    updateRole: (id: number) => `/v1/students/${String(id)}/role`,
    addCoins: (id: number) => `/v1/students/${String(id)}/coins`,
  },
}
