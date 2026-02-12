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

// Course types
export type CourseStatus = 'hidden' | 'published'

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
  status: CourseStatus
  created_by?: number | null
  created_with?: string | null
  created_at?: string | null
  updated_at?: string | null
  lectures_with_audio_count?: number
  topics_count?: number
  student?: {
    id: number
    name: string
    email: string | null
  } | null
  professor?: {
    id: number
    name: string
    title: string
    department_id: number
    specialization: string
    image_url: string | null
  } | null
  department?: {
    id: number
    name: string
    code: string
    faculty_id: number | null
    faculty_name: string | null
  } | null
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

export interface CourseCreate {
  code: string
  title: string
  department_id?: number | null
  level?: string | null
  credits?: number
  professor_id?: number | null
  description: string
  lectures_per_week?: number
  total_weeks?: number
  created_with?: string | null
}

export interface CourseUpdate {
  code?: string
  title?: string
  department_id?: number | null
  level?: string | null
  credits?: number
  professor_id?: number | null
  description?: string
  lectures_per_week?: number
  total_weeks?: number
  status?: CourseStatus
}

export interface CoursesListResponse {
  items: Course[]
  total: number
  page: number
  size: number
  pages: number
}

// Brief Lecture info for course's lectures endpoint
export interface LectureBrief {
  id: number
  course_id: number
  topic_id: number
  title: string
  summary: string | null
  audio_url?: string | null
  audio_download_url?: string | null
  transcript_url?: string | null
}

export interface CourseLecturesResponse {
  course_id: number
  lectures: LectureBrief[]
  total: number
}

export interface CourseGenerateRequest {
  partial_attributes?: Record<string, unknown>
  freeform_prompt?: string
}

// Department types
export interface Department {
  id: number
  name: string
  code: string
  faculty_id: number | null
  faculty_name: string | null
  description: string | null
}

export interface DepartmentCreate {
  name: string
  code: string
  faculty_id?: number | null
  description?: string | null
}

export interface DepartmentUpdate {
  name: string
  code: string
  faculty_id?: number | null
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
  partial_attributes?: Record<string, unknown>
  freeform_prompt?: string
  department_id?: number
}

// Department nested endpoints response types
export interface DepartmentProfessor {
  id: number
  name: string
  title: string
  specialization: string
  image_url: string
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

// Brief Department info for nested responses
export interface DepartmentBrief {
  id: number
  name: string
  code: string
  faculty_id: number | null
  faculty_name: string | null
}

// Lecture types
export interface Lecture {
  id: number
  course_id: number
  topic_id: number
  revision: number
  title: string
  content: string
  summary: string | null
  audio_url: string | null
  audio_download_url?: string | null
  transcript_url: string | null
  word_count: number | null
  duration: number | null
  created_by?: number | null
  created_with?: string | null
  created_at?: string | null
  updated_at?: string | null
  student?: {
    id: number
    name: string
    email: string | null
  } | null
}

export interface LectureCreate {
  course_id: number
  topic_id: number
  title: string
  content: string
  summary?: string | null
  audio_url?: string | null
  transcript_url?: string | null
  revision?: number | null
  word_count?: number | null
}

export interface LectureUpdate {
  course_id?: number
  topic_id?: number
  title?: string
  content?: string
  summary?: string | null
  audio_url?: string | null
  transcript_url?: string | null
  revision?: number | null
  word_count?: number | null
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
  image_created_with?: string | null
  voice_id?: number | null
  created_by?: number | null
  created_with?: string | null
  created_at?: string | null
  updated_at?: string | null
  student?: {
    id: number
    name: string
    email: string | null
  } | null
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

// Topic types
export type TopicContent = Record<string, string | string[]> | null

export interface Topic {
  id: number
  title: string
  course_id: number
  week: number
  order: number
  content: TopicContent
  created_by?: number | null
  created_with?: string | null
  created_at?: string | null
}

export interface TopicCreate {
  title: string
  course_id: number
  week: number
  order: number
  content: TopicContent
}

export interface TopicUpdate {
  title?: string
  course_id?: number
  week?: number
  order?: number
  content?: TopicContent
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

// Faculty types
export interface Faculty {
  id: number
  name: string
  description: string | null
}

export interface FacultiesListResponse {
  items: Faculty[]
  total: number
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
  verified_languages: Array<Record<string, unknown>>
  popularity_score: number | null
  last_updated: string | null
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

// Error response type
export interface APIError {
  detail: string
  message?: string
  status_code?: number
  path?: string
  timestamp?: string
}

// Student types
export interface Student {
  id: number
  name: string
  email: string | null
  auth0_sub: string | null
  role: 'viewer' | 'creator' | 'admin'
  coins: number
  is_active: boolean
}

export interface StudentUpdate {
  name?: string
  email?: string
}

export interface StudentRoleUpdate {
  role: 'viewer' | 'creator' | 'admin'
}

export interface StudentCoinsAdd {
  amount: number
}

// Job types
export interface JobResponse {
  id: number
  kind: string
  status: string
  attempts: number
  max_attempts: number
  priority?: number
  run_after?: string
  message?: string
}

// Quickstart types
export interface QuickstartCourseBrief {
  id: number
  code: string
  title: string
  description: string
  professor_name: string | null
  professor_image_url: string | null
}

export interface QuickstartMatchRequest {
  query: string
}

export interface QuickstartMatchResponse {
  action: 'SELECT' | 'GENERATE'
  matched_courses: QuickstartCourseBrief[]
  reasoning: string
}

export interface QuickstartStartRequest {
  query: string
}

export interface QuickstartStartResponse {
  course_id: number
  professor_id: number
  department_id: number
  course_title: string
  course_code: string
  course_description: string
}

export interface QuickstartProfessorDetail {
  id: number
  name: string
  title: string
  specialization: string
  description: string | null
  personality: string | null
  teaching_style: string | null
  background: string | null
  gender: string | null
  age: number | null
  accent: string | null
  image_url: string | null
  voice_preview_url: string | null
  voice_id: number | null
}

export interface QuickstartProfessorResponse {
  professor: QuickstartProfessorDetail
  course_id: number
  course_title: string
}

export interface IntroAudioRequest {
  professor_id: number
  course_title: string
}

export interface IntroAudioResponse {
  audio_data_uri: string
  text: string
}

export interface QuickstartProfessorActionRequest {
  professor_id: number
  course_id: number
}

export interface QuickstartRegenerateProfessorRequest {
  course_id: number
  department_id: number
  freeform_prompt?: string
}

export interface QuickstartFinalizeRequest {
  course_id: number
}

export interface QuickstartFinalizeResponse {
  course_id: number
  topics_job_id: number
  message: string
}

// Featured items
export interface FeaturedItem {
  id: number
  item_type: 'lecture' | 'professor' | 'department'
  item_id: number
  language: string
  display_order: number
  created_at: string | null
}

export interface FeaturedItemCreate {
  item_type: 'lecture' | 'professor' | 'department'
  item_id: number
  language?: string
  display_order?: number
}

// Stats
export interface PlatformStats {
  course_count: number
  lecture_count: number
  audio_hours: number
}

// Recent / enriched lecture (homepage)
export interface RecentLecture {
  id: number
  title: string
  summary: string | null
  audio_url: string | null
  duration: number | null
  course_id: number
  course_code: string | null
  course_title: string | null
  topic_id: number
  topic_title: string | null
  topic_week: number | null
  professor_id: number | null
  professor_name: string | null
  professor_image_url: string | null
  professor_accent: string | null
  professor_specialization: string | null
  department_name: string | null
  created_at: string | null
}

// Search
export interface LectureSearchResult {
  id: number
  title: string
  summary: string | null
  course_id: number
  course_title: string | null
  course_code: string | null
  professor_name: string | null
  department_name: string | null
  audio_url: string | null
  duration: number | null
}

export interface CourseSearchResult {
  id: number
  code: string
  title: string
  description: string | null
  level: string | null
  department_name: string | null
  professor_name: string | null
  status: string | null
}

export interface ProfessorSearchResult {
  id: number
  name: string
  title: string | null
  specialization: string | null
  department_name: string | null
  image_url: string | null
}

export interface DepartmentSearchResult {
  id: number
  name: string
  code: string
  description: string | null
}

export interface TopicSearchResult {
  id: number
  title: string
  week: number
  course_id: number
  course_title: string | null
  course_code: string | null
}

export interface SearchResponse {
  query: string
  lectures: LectureSearchResult[]
  courses: CourseSearchResult[]
  professors: ProfessorSearchResult[]
  departments: DepartmentSearchResult[]
  topics: TopicSearchResult[]
}
