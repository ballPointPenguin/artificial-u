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
  department: string
  title: string
  email: string
  specialization: string
  bio: string
  image_url: string | null
  created_at: string
  updated_at: string
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
  created_at: string
  updated_at: string
}

export type DepartmentsList = PaginatedResponse<Department>

// Course types
export interface Course {
  id: number
  code: string
  title: string
  department: string
  department_id: number
  professor_id: number
  professor_name: string
  description: string
  credit_hours: number
  semester: string
  created_at: string
  updated_at: string
}

export type CoursesList = PaginatedResponse<Course>

// Lecture types
export interface Lecture {
  id: number
  title: string
  description: string
  course_id: number
  course_title: string
  professor_id: number
  professor_name: string
  date: string
  duration: number
  status: string
  audio_url: string | null
  transcript: string | null
  created_at: string
  updated_at: string
}

export type LecturesList = PaginatedResponse<Lecture>

// Error response type
export interface APIError {
  detail: string
  status_code?: number
  path?: string
  timestamp?: string
}
