import { type JSX, Show, createEffect, createSignal } from 'solid-js'
import { generateDepartment } from '../api/services/department-service'
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
  const [isGenerating, setIsGenerating] = createSignal(false)
  const [generateError, setGenerateError] = createSignal<string | null>(null)
  const [formData, setFormData] = createSignal<DepartmentFormData>({
    name: '',
    code: '',
    faculty: '',
    description: '',
  })

  // Keep formData in sync with props.department (for edit mode)
  createEffect(() => {
    setFormData({
      name: props.department?.name || '',
      code: props.department?.code || '',
      faculty: props.department?.faculty || '',
      description: props.department?.description || '',
    })
  })

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

  const handleInput = (e: Event) => {
    const target = e.target as HTMLInputElement | HTMLTextAreaElement
    setFormData({ ...formData(), [target.name]: target.value })
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

  const handleGenerate = async () => {
    setGenerateError(null)
    setIsGenerating(true)
    setValidationErrors({})
    try {
      // Validate before sending
      const fakeForm = document.createElement('form')
      for (const [k, v] of Object.entries(formData())) {
        const input = document.createElement('input')
        input.name = k
        input.value = v
        fakeForm.appendChild(input)
      }
      const generated = await generateDepartment(formData())
      setFormData({
        name: generated.name,
        code: generated.code,
        faculty: generated.faculty,
        description: generated.description,
      })
    } catch (err: unknown) {
      let message = 'Failed to generate department'
      if (
        typeof err === 'object' &&
        err !== null &&
        'message' in err &&
        typeof (err as { message?: unknown }).message === 'string'
      ) {
        message = (err as { message: string }).message
      }
      setGenerateError(message)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleClear = () => {
    setFormData({
      name: '',
      code: '',
      faculty: '',
      description: '',
    })
    setValidationErrors({})
    setGenerateError(null)
  }

  const isDisabled = () => props.isSubmitting || isGenerating()

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
          value={formData().name}
          onInput={handleInput}
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().name,
          }}
          disabled={isDisabled()}
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
          value={formData().code}
          onInput={handleInput}
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().code,
          }}
          disabled={isDisabled()}
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
          value={formData().faculty}
          onInput={handleInput}
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().faculty,
          }}
          disabled={isDisabled()}
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
          value={formData().description}
          onInput={handleInput}
          class="arcane-input"
          classList={{
            'border-red-500': !!validationErrors().description,
          }}
          disabled={isDisabled()}
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
      <Show when={generateError()}>
        <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded">
          {generateError()}
        </div>
      </Show>

      <div class="flex justify-end space-x-3">
        <Button
          type="button"
          variant="outline"
          onClick={props.onCancel}
          disabled={isDisabled()}
        >
          Cancel
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={handleClear}
          disabled={isDisabled()}
        >
          Clear
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            void handleGenerate()
          }}
          disabled={isDisabled()}
        >
          <span class="flex items-center gap-2">
            <span class="inline-block align-middle">
              {/* Magic wand SVG icon */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5 text-mystic-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <title>Generate</title>
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M15.5 8.5l-8 8m0 0L3 21l4.5-4.5m0 0l8-8M19 5l.01-.01M15 3l.01-.01M21 9l.01-.01M17 13l.01-.01"
                />
              </svg>
            </span>
            <span>
              {isGenerating() ? (
                <span class="flex items-center gap-1">
                  <span class="inline-block w-4 h-4 border-2 border-mystic-300 border-t-transparent rounded-full animate-spin" />
                  Generating...
                </span>
              ) : (
                'Generate'
              )}
            </span>
          </span>
        </Button>
        <Button type="submit" variant="primary" disabled={isDisabled()}>
          {props.isSubmitting
            ? 'Saving...'
            : props.department !== undefined
              ? 'Update'
              : 'Save'}
        </Button>
      </div>
    </form>
  )
}

export default DepartmentForm
