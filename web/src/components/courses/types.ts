// Form data interface for Course creation and editing
export interface CourseFormData {
  code: string
  title: string
  department_id: number | null // Will be number for submission, null if not selected
  level: string
  credits: number | null
  professor_id: number | null // Will be number for submission, null if not selected
  description: string
  lectures_per_week?: number | null // Optional field
  total_weeks?: number | null // Optional field

  // Add any other fields that are part of the form but maybe not directly in CourseCreate/Update initially
  // For example, a freeform prompt for generation if not directly mapping all fields to CourseGenerateRequest.partial_attributes
  generate_prompt?: string
}
