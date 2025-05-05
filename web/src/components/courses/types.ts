import type { Course, CourseTopic } from '../../api/types'

// Form data interface matching the API model
export interface CourseFormData {
  code: string
  title: string
  department_id: number | null
  level: string
  credits: number
  professor_id: number | null
  description: string
  lectures_per_week: number
  total_weeks: number
  topics: CourseTopic[]
}

export interface ValidationErrors {
  [key: string]: string
}

export interface FormProps {
  course?: Course
  onSubmit: (data: CourseFormData) => void | Promise<void>
  onCancel: () => void
  isSubmitting: boolean
  error: string
}

export interface BasicInfoProps {
  disabled?: boolean
}

export interface DescriptionProps {
  disabled?: boolean
}

export interface TopicsProps {
  disabled?: boolean
}

export interface WeekTopicsProps {
  week: number
  lecturesPerWeek: number
  disabled?: boolean
}

export interface TopicInputProps {
  week: number
  order: number
  disabled?: boolean
}

// Default form data
export const defaultFormData: CourseFormData = {
  code: '',
  title: '',
  department_id: null,
  level: 'Undergraduate',
  credits: 3,
  professor_id: null,
  description: '',
  lectures_per_week: 1,
  total_weeks: 14,
  topics: Array.from({ length: 14 }, (_, weekIdx) => ({
    week_number: weekIdx + 1,
    order_in_week: 1,
    title: '',
  })),
}
