import {
  type Component,
  For,
  Show,
  createEffect,
  createResource,
  createSignal,
} from 'solid-js'
import { getDepartments } from '../api/services/department-service'
import { getProfessors } from '../api/services/professor-service'
import type { Course } from '../api/types'
import { Button } from './ui/Button'

// Form data interface matching the API model
export interface CourseFormData {
  code: string
  title: string
  department_id: number
  level: string
  credits: number
  professor_id: number
  description: string
  lectures_per_week: number
  total_weeks: number
  syllabus: string | null
}

const defaultFormData: CourseFormData = {
  code: '',
  title: '',
  department_id: 0,
  level: 'Undergraduate',
  credits: 3,
  professor_id: 0,
  description: '',
  lectures_per_week: 1,
  total_weeks: 14,
  syllabus: '',
}

interface CourseFormProps {
  course?: Course
  onSubmit: (data: CourseFormData) => void | Promise<void>
  onCancel: () => void
  isSubmitting: boolean
  error: string
}

const CourseForm: Component<CourseFormProps> = (props) => {
  const [validationErrors, setValidationErrors] = createSignal<
    Record<string, string>
  >({})

  const [formData, setFormData] = createSignal<CourseFormData>(defaultFormData)

  // Fetch departments for dropdown
  const [departments] = createResource(() => getDepartments({ size: 100 }))

  // Fetch professors for dropdown
  const [professors] = createResource(() => getProfessors({ size: 100 }))

  // Update form data when course changes or on initial load
  createEffect(() => {
    if (props.course) {
      const course = props.course
      setFormData({
        ...defaultFormData,
        code: course.code,
        title: course.title,
        department_id: 0, // Will be set correctly if available
        level: course.level || 'Undergraduate',
        credits: course.credits || 3,
        professor_id: course.professor_id,
        description: course.description || '',
        lectures_per_week: course.lectures_per_week || 1,
        total_weeks: course.total_weeks || 14,
        syllabus: course.syllabus || null,
      })
    }
  })

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    const data = formData()

    if (!data.code || data.code.trim() === '') {
      errors.code = 'Course code is required'
    }

    if (!data.title || data.title.trim() === '') {
      errors.title = 'Course title is required'
    }

    if (!data.department_id || data.department_id === 0) {
      errors.department_id = 'Department is required'
    }

    if (!data.professor_id || data.professor_id === 0) {
      errors.professor_id = 'Professor is required'
    }

    if (!data.description || data.description.trim() === '') {
      errors.description = 'Description is required'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleChange = (
    e: Event & {
      currentTarget: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    }
  ) => {
    const { name, value, type } = e.currentTarget

    setFormData((prev: CourseFormData) => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value,
    }))
  }

  const handleSubmit = (e: Event) => {
    e.preventDefault()

    if (validateForm()) {
      void props.onSubmit(formData())
    }
  }

  return (
    <form onSubmit={handleSubmit} class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label
            for="code"
            class="block text-sm font-medium mb-1 text-parchment-300"
          >
            Course Code*
          </label>
          <input
            id="code"
            name="code"
            type="text"
            required
            value={formData().code}
            onInput={handleChange}
            placeholder="e.g., CS101"
            class="arcane-input"
            classList={{
              'border-red-500': !!validationErrors().code,
            }}
            disabled={props.isSubmitting}
          />
          <Show when={validationErrors().code}>
            <p class="mt-1 text-sm text-red-600">{validationErrors().code}</p>
          </Show>
        </div>

        <div>
          <label
            for="title"
            class="block text-sm font-medium mb-1 text-parchment-300"
          >
            Course Title*
          </label>
          <input
            id="title"
            name="title"
            type="text"
            required
            value={formData().title}
            onInput={handleChange}
            placeholder="Introduction to Computer Science"
            class="arcane-input"
            classList={{
              'border-red-500': !!validationErrors().title,
            }}
            disabled={props.isSubmitting}
          />
          <Show when={validationErrors().title}>
            <p class="mt-1 text-sm text-red-600">{validationErrors().title}</p>
          </Show>
        </div>

        <div>
          <label
            for="department_id"
            class="block text-sm font-medium mb-1 text-parchment-300"
          >
            Department*
          </label>
          <select
            id="department_id"
            name="department_id"
            required
            value={formData().department_id}
            onChange={handleChange}
            class="arcane-input"
            classList={{
              'border-red-500': !!validationErrors().department_id,
            }}
            disabled={props.isSubmitting || departments.loading}
          >
            <option value="0" disabled>
              Select a department
            </option>
            <Show when={!departments.loading && departments()}>
              {(depts) => (
                <>
                  <For each={depts().items}>
                    {(dept) => (
                      <option value={dept.id}>
                        {dept.name} ({dept.code})
                      </option>
                    )}
                  </For>
                </>
              )}
            </Show>
          </select>
          <Show when={departments.loading}>
            <p class="text-parchment-400 text-sm mt-1">
              Loading departments...
            </p>
          </Show>
          <Show when={validationErrors().department_id}>
            <p class="mt-1 text-sm text-red-600">
              {validationErrors().department_id}
            </p>
          </Show>
        </div>

        <div>
          <label
            for="professor_id"
            class="block text-sm font-medium mb-1 text-parchment-300"
          >
            Professor*
          </label>
          <select
            id="professor_id"
            name="professor_id"
            required
            value={formData().professor_id}
            onChange={handleChange}
            class="arcane-input"
            classList={{
              'border-red-500': !!validationErrors().professor_id,
            }}
            disabled={props.isSubmitting || professors.loading}
          >
            <option value="0" disabled>
              Select a professor
            </option>
            <Show when={!professors.loading && professors()}>
              {(profs) => (
                <>
                  <For each={profs().items}>
                    {(prof) => (
                      <option value={prof.id}>
                        {prof.name} - {prof.title}
                      </option>
                    )}
                  </For>
                </>
              )}
            </Show>
          </select>
          <Show when={professors.loading}>
            <p class="text-parchment-400 text-sm mt-1">Loading professors...</p>
          </Show>
          <Show when={validationErrors().professor_id}>
            <p class="mt-1 text-sm text-red-600">
              {validationErrors().professor_id}
            </p>
          </Show>
        </div>

        <div>
          <label
            for="level"
            class="block text-sm font-medium mb-1 text-parchment-300"
          >
            Level*
          </label>
          <select
            id="level"
            name="level"
            required
            value={formData().level}
            onChange={handleChange}
            class="arcane-input"
            disabled={props.isSubmitting}
          >
            <option value="Undergraduate">Undergraduate</option>
            <option value="Graduate">Graduate</option>
            <option value="Doctoral">Doctoral</option>
            <option value="Certificate">Certificate</option>
          </select>
        </div>

        <div>
          <label
            for="credits"
            class="block text-sm font-medium mb-1 text-parchment-300"
          >
            Credits*
          </label>
          <input
            id="credits"
            name="credits"
            type="number"
            min="0"
            max="12"
            required
            value={formData().credits}
            onInput={handleChange}
            class="arcane-input"
            disabled={props.isSubmitting}
          />
        </div>

        <div>
          <label
            for="lectures_per_week"
            class="block text-sm font-medium mb-1 text-parchment-300"
          >
            Lectures Per Week*
          </label>
          <input
            id="lectures_per_week"
            name="lectures_per_week"
            type="number"
            min="1"
            max="7"
            required
            value={formData().lectures_per_week}
            onInput={handleChange}
            class="arcane-input"
            disabled={props.isSubmitting}
          />
        </div>

        <div>
          <label
            for="total_weeks"
            class="block text-sm font-medium mb-1 text-parchment-300"
          >
            Total Weeks*
          </label>
          <input
            id="total_weeks"
            name="total_weeks"
            type="number"
            min="1"
            max="52"
            required
            value={formData().total_weeks}
            onInput={handleChange}
            class="arcane-input"
            disabled={props.isSubmitting}
          />
        </div>
      </div>

      <div>
        <label
          for="description"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Description*
        </label>
        <textarea
          id="description"
          name="description"
          rows={4}
          required
          value={formData().description}
          onInput={handleChange}
          placeholder="Course description..."
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().description,
          }}
          disabled={props.isSubmitting}
        />
        <Show when={validationErrors().description}>
          <p class="mt-1 text-sm text-red-600">
            {validationErrors().description}
          </p>
        </Show>
      </div>

      <div>
        <label
          for="syllabus"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Syllabus URL
        </label>
        <input
          id="syllabus"
          name="syllabus"
          type="url"
          value={formData().syllabus || ''}
          onInput={handleChange}
          placeholder="https://example.com/syllabus.pdf"
          class="arcane-input"
          disabled={props.isSubmitting}
        />
      </div>

      <Show when={props.error}>
        <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded">
          {props.error}
        </div>
      </Show>

      <div class="flex justify-end space-x-3">
        <Button
          type="button"
          variant="outline"
          onClick={props.onCancel}
          disabled={props.isSubmitting}
        >
          Cancel
        </Button>
        <Button type="submit" variant="primary" disabled={props.isSubmitting}>
          {props.isSubmitting
            ? 'Saving...'
            : props.course !== undefined
              ? 'Update Course'
              : 'Create Course'}
        </Button>
      </div>
    </form>
  )
}

export default CourseForm
