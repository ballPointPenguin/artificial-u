/**
 * TypeScript definitions for API request/response types
 */

// Common pagination and response wrapper types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// API Info response
export interface APIInfo {
  name: string
  version: string
  description: string
  docs_url: string
}

// Health check response
export interface HealthCheckResponse {
  status: string
  version: string
  timestamp: string
}

// Professor types
export interface Professor {
  id: number
  name: string
  title: string
  department: string
  specialization: string
  background: string
  personality: string
  teaching_style: string
  gender: string | null
  accent: string | null
  description: string | null
  age: number | null
  voice_settings: {
    voice_id: string
    stability: number
    clarity: number
  } | null
  image_path: string | null
}

export type ProfessorsList = PaginatedResponse<Professor>

export interface ProfessorCourse {
  id: number
  code: string
  title: string
  department: string
  description: string
  credit_hours: number
  semester: string
}

export interface ProfessorCoursesResponse {
  professor_id: number
  professor_name: string
  courses: ProfessorCourse[]
}

export interface ProfessorLecture {
  id: number
  title: string
  course_id: number
  course_title: string
  date: string
  duration: number
  status: string
}

export interface ProfessorLecturesResponse {
  professor_id: number
  professor_name: string
  lectures: ProfessorLecture[]
}

// Department types
export interface Department {
  id: number
  name: string
  code: string
  faculty: string
  description: string
  created_at?: string
  updated_at?: string
}

export type DepartmentsList = PaginatedResponse<Department>

// Course types
export interface Course {
  id: number
  code: string
  title: string
  department: string
  level: string
  credits: number
  professor_id: number
  description: string
  lectures_per_week: number
  total_weeks: number
  syllabus: string | null
  generated_at: string
}

export type CoursesList = PaginatedResponse<Course>

// Lecture types
export interface Lecture {
  id: number
  title: string
  course_id: number
  week_number: number
  order_in_week: number
  description: string
  content: string
  audio_url: string | null
  generated_at: string
}

export type LecturesList = PaginatedResponse<Lecture>

// Voice types
export interface Voice {
  id: number
  voice_id: string
  name: string
  accent: string | null
  gender: string | null
  age: string | null
  descriptive: string | null
  use_case: string | null
  category: string | null
  language: string | null
  locale: string | null
  description: string | null
  preview_url: string | null
  verified_languages: Record<string, unknown>
  popularity_score: number | null
  last_updated: string
}

// Error response type
export interface APIError {
  detail: string
  status_code?: number
  path?: string
  timestamp?: string
}
