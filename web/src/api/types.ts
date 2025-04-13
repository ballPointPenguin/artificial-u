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
  title: string | null
  specialization: string | null
  background: string | null
  personality: string | null
  teaching_style: string | null
  gender: string | null
  accent: string | null
  description: string | null
  age: number | null
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

// Brief Department info for nested responses
export interface DepartmentBrief {
  id: number
  name: string
  code: string
  faculty: string
}

// Course types
export interface Course {
  id: number
  code: string
  title: string
  level: string | null
  credits: number | null
  professor_id: number
  description: string | null
  lectures_per_week: number | null
  total_weeks: number | null
  syllabus: string | null
  generated_at: string
}

export type CoursesList = PaginatedResponse<Course>

// Brief Professor info for nested responses
export interface ProfessorBrief {
  id: number
  name: string
  title: string
  department_id: number // Assuming this is available from backend
  specialization: string
}

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

// Brief Lecture info for nested responses
export interface LectureBrief {
  id: number
  title: string
  week_number: number
  order_in_week: number
  description: string
  audio_url: string | null
}

// Updated LecturesList to use LectureBrief for Course detail view
export interface LecturesList {
  course_id: number
  lectures: LectureBrief[]
  total: number
}

// Voice types
export interface Voice {
  id: number
  el_voice_id: string
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
