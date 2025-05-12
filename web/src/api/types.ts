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
  api_version: string
  timestamp: number
}

// Professor types
export interface Professor {
  id: number
  name: string
  title: string | null
  department_id: number | null
  specialization: string | null
  background: string | null
  personality: string | null
  teaching_style: string | null
  gender: string | null
  accent: string | null
  description: string | null
  age: number | null
  image_url: string | null
  voice_id?: number | null
}

export interface ProfessorCreate {
  name?: string | null
  title?: string | null
  department_id?: number | null
  specialization?: string | null
  background?: string | null
  personality?: string | null
  teaching_style?: string | null
  gender?: string | null
  accent?: string | null
  description?: string | null
  age?: number | null
  image_url?: string | null
  voice_id?: number | null
}

export interface ProfessorUpdate {
  name?: string | null
  title?: string | null
  department_id?: number | null
  specialization?: string | null
  background?: string | null
  personality?: string | null
  teaching_style?: string | null
  gender?: string | null
  accent?: string | null
  description?: string | null
  age?: number | null
  image_url?: string | null
  voice_id?: number | null
}

export interface ProfessorsListResponse {
  items: Professor[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ProfessorCourseBrief {
  id: number
  code: string
  title: string
  department_id?: number | null
  level: string
  credits: number
}

export interface ProfessorCoursesResponse {
  professor_id: number
  courses: ProfessorCourseBrief[]
  total: number
}

export interface ProfessorLecturesResponse {
  professor_id: number
  lectures: LectureBrief[]
  total: number
}

export interface ProfessorGenerateRequest {
  partial_attributes?: Record<string, unknown>
  freeform_prompt?: string
}

// Department types
export interface Department {
  id: number
  name: string
  code: string
  faculty: string | null
  description: string | null
}

export interface DepartmentCreate {
  name: string
  code: string
  faculty?: string | null
  description?: string | null
}

export interface DepartmentUpdate {
  name: string
  code: string
  faculty?: string | null
  description?: string | null
}

export interface DepartmentsListResponse {
  items: Department[]
  total: number
  page: number
  size: number
  pages: number
}

export interface DepartmentGenerateRequest {
  name?: string
  code?: string
  faculty?: string
  description?: string
  freeform_prompt?: string
}

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
  department_id: number
  level: string
  credits: number
  professor_id: number
  description: string
  lectures_per_week: number
  total_weeks: number
}

export type CoursesList = PaginatedResponse<Course>

// Brief Professor info for nested responses
export interface ProfessorBrief {
  id: number
  name: string
  title: string
  specialization: string
  department_id: number
}

// Matches Python CourseCreate which is based on CourseBase
export interface CourseCreate {
  code: string
  title: string
  department_id: number
  level: string
  credits?: number
  professor_id: number
  description: string
  lectures_per_week?: number
  total_weeks?: number
}

// Matches Python CourseUpdate
export interface CourseUpdate {
  code?: string
  title?: string
  department_id?: number
  level?: string
  credits?: number
  professor_id?: number
  description?: string
  lectures_per_week?: number
  total_weeks?: number
}

// Matches Python CoursesListResponse
export interface CoursesListResponse {
  items: Course[]
  total: number
  page: number
  size: number
  pages: number
}

// Brief Lecture info for course's lectures endpoint (matches Python model)
export interface LectureBrief {
  id: number
  title: string
  week_number: number
  order_in_week: number
  description: string
}

// Matches Python CourseLecturesResponse
export interface CourseLecturesResponse {
  course_id: number
  lectures: LectureBrief[]
  total: number
}

// Topic types
export interface Topic {
  id: number
  title: string
  course_id: number
  week: number
  order: number
}

export interface TopicCreate {
  title: string
  course_id: number
  week: number
  order: number
}

export interface TopicUpdate {
  title?: string
  course_id?: number
  week?: number
  order?: number
}

export interface TopicList {
  items: Topic[]
  total: number
  page: number
  page_size: number
}

export interface TopicsGenerateRequest {
  course_id: number
  freeform_prompt?: string
}

// Lecture types (updated to match Python API)
export interface Lecture {
  id: number
  course_id: number
  topic_id: number
  revision: number
  content: string
  summary: string | null
  audio_url: string | null
  transcript_url: string | null
}

export interface LectureCreate {
  course_id: number
  topic_id: number
  content: string
  summary?: string | null
  audio_url?: string | null
  transcript_url?: string | null
  revision?: number | null
}

export interface LectureUpdate {
  course_id?: number
  topic_id?: number
  content?: string
  summary?: string | null
  audio_url?: string | null
  transcript_url?: string | null
  revision?: number | null
}

export interface LectureList {
  items: Lecture[]
  total: number
  page: number
  page_size: number
}

export interface LectureGenerateRequest {
  partial_attributes?: Record<string, unknown>
  freeform_prompt?: string
}

export interface AudioRedirectResponse {
  url: string
}

// Voice types
export interface Voice {
  id: number
  el_voice_id: string | null
  name: string | null
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
  verified_languages: Record<string, unknown> | null
  popularity_score: number | null
  last_updated: string | null
}

// Error response type
export interface APIError {
  detail: string
  status_code?: number
  path?: string
  timestamp?: string
}

// Department nested endpoints response types
export interface DepartmentProfessor {
  id: number
  name: string
  title: string
  specialization: string
}

export interface DepartmentProfessorsResponse {
  department_id: number
  professors: DepartmentProfessor[]
  total: number
}

export interface DepartmentCourse {
  id: number
  code: string
  title: string
  level: string
  credits: number
  professor_id?: number
}

export interface DepartmentCoursesResponse {
  department_id: number
  courses: DepartmentCourse[]
  total: number
}

export interface CourseGenerateRequest {
  partial_attributes?: Record<string, unknown>
  freeform_prompt?: string
}

export interface PaginatedVoices {
  items: Voice[]
  total: number
  limit: number
  offset: number
}

export interface ManualVoiceAssignmentPayload {
  el_voice_id: string
}

export interface VoiceListParams {
  gender?: string
  accent?: string
  age?: string
  language?: string
  use_case?: string
  category?: string
  limit?: number
  offset?: number
}
