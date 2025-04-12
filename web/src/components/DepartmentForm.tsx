import { type JSX, Show, createSignal } from 'solid-js'
import type { Department } from '../api/types'
import { Button } from './ui/Button'

// Form data interface matching the API model
interface DepartmentFormData {
  name: string
  code: string
  faculty: string
  description: string
}

interface DepartmentFormProps {
  department?: Department & Partial<DepartmentFormData>
  onSubmit: (data: FormData) => void
  onCancel: () => void
  isSubmitting: boolean
  error?: string
}

const DepartmentForm = (props: DepartmentFormProps) => {
  const [validationErrors, setValidationErrors] = createSignal<
    Record<string, string>
  >({})

  const validateForm = (form: HTMLFormElement): boolean => {
    const newErrors: Record<string, string> = {}
    const formData = new FormData(form)

    const name = formData.get('name') as string
    const code = formData.get('code') as string
    const faculty = formData.get('faculty') as string
    const description = formData.get('description') as string

    if (!name || name.trim() === '') {
      newErrors.name = 'Department name is required'
    }

    if (!code || code.trim() === '') {
      newErrors.code = 'Department code is required'
    } else if (code.length < 2 || code.length > 10) {
      newErrors.code = 'Code must be between 2 and 10 characters'
    }

    if (!faculty || faculty.trim() === '') {
      newErrors.faculty = 'Faculty is required'
    }

    if (!description || description.trim() === '') {
      newErrors.description = 'Description is required'
    }

    setValidationErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit: JSX.EventHandler<HTMLFormElement, SubmitEvent> = (
    event
  ) => {
    event.preventDefault()
    const form = event.currentTarget

    if (validateForm(form)) {
      const formData = new FormData(form)
      props.onSubmit(formData)
    }
  }

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <div>
        <label
          for="name"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Department Name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          value={props.department?.name || ''}
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().name,
          }}
        />
        <Show when={validationErrors().name}>
          <p class="mt-1 text-sm text-red-600">{validationErrors().name}</p>
        </Show>
      </div>

      <div>
        <label
          for="code"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Department Code
        </label>
        <input
          id="code"
          name="code"
          type="text"
          value={props.department?.code || ''}
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().code,
          }}
        />
        <Show when={validationErrors().code}>
          <p class="mt-1 text-sm text-red-600">{validationErrors().code}</p>
        </Show>
      </div>

      <div>
        <label
          for="faculty"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Faculty
        </label>
        <input
          id="faculty"
          name="faculty"
          type="text"
          value={props.department?.faculty || ''}
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().faculty,
          }}
        />
        <Show when={validationErrors().faculty}>
          <p class="mt-1 text-sm text-red-600">{validationErrors().faculty}</p>
        </Show>
      </div>

      <div>
        <label
          for="description"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Description
        </label>
        <textarea
          id="description"
          name="description"
          rows={4}
          value={props.department?.description || ''}
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().description,
          }}
        />
        <Show when={validationErrors().description}>
          <p class="mt-1 text-sm text-red-600">
            {validationErrors().description}
          </p>
        </Show>
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
            : props.department !== undefined
              ? 'Update Department'
              : 'Create Department'}
        </Button>
      </div>
    </form>
  )
}

export default DepartmentForm
