import { type ParentProps, createContext, useContext } from 'solid-js'
import { createStore } from 'solid-js/store'
import type { CourseTopic } from '../../api/types'
import { defaultFormData } from './types.js'
import type { CourseFormData, ValidationErrors } from './types.js'

interface CourseFormProviderProps extends ParentProps {
  initialData?: CourseFormData
}

interface CourseFormContextValue {
  form: CourseFormData
  errors: ValidationErrors
  updateForm: (path: string, value: unknown) => void
  updateTopicTitle: (weekNum: number, orderInWeek: number, title: string) => void
  validateForm: () => boolean
  resetForm: () => void
  resetTopics: (topics: CourseTopic[]) => void
}

const FormContext = createContext<CourseFormContextValue>()

export function CourseFormProvider(props: CourseFormProviderProps) {
  const [form, setForm] = createStore<CourseFormData>(props.initialData || defaultFormData)
  const [errors, setErrors] = createStore<ValidationErrors>({})

  // Form update functions - idiomatic SolidJS approach
  const updateForm = (path: string, value: unknown) => {
    // This is the idiomatic way: use type assertions but keep it simple
    // @ts-expect-error: SetStoreFunction has complex typing that's hard to satisfy perfectly
    setForm(path, value)
  }

  const updateTopicTitle = (weekNum: number, orderInWeek: number, title: string) => {
    // For nested updates with a function, the typing works better
    setForm('topics', (topics: CourseTopic[]) =>
      topics.map((topic: CourseTopic) =>
        topic.week_number === weekNum && topic.order_in_week === orderInWeek
          ? { ...topic, title }
          : topic
      )
    )
  }

  // Special method to completely replace the topics array
  // This ensures proper reactivity when array references change
  const resetTopics = (topics: CourseTopic[]) => {
    // Using a function to replace the entire array
    setForm('topics', () => [...topics])
  }

  // Validation function
  const validateForm = () => {
    const newErrors: ValidationErrors = {}

    if (!form.code || form.code.trim() === '') {
      newErrors.code = 'Course code is required'
    }

    if (!form.title || form.title.trim() === '') {
      newErrors.title = 'Course title is required'
    }

    if (!form.department_id) {
      newErrors.department_id = 'Department is required'
    }

    if (!form.professor_id) {
      newErrors.professor_id = 'Professor is required'
    }

    if (!form.description || form.description.trim() === '') {
      newErrors.description = 'Description is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Reset form to initial state
  const resetForm = () => {
    setForm(props.initialData || defaultFormData)
    setErrors({})
  }

  const value: CourseFormContextValue = {
    form,
    errors,
    updateForm,
    updateTopicTitle,
    validateForm,
    resetForm,
    resetTopics,
  }

  return <FormContext.Provider value={value}>{props.children}</FormContext.Provider>
}

export function useCourseForm() {
  const context = useContext(FormContext)
  if (!context) {
    throw new Error('useCourseForm must be used within a CourseFormProvider')
  }
  return context
}
