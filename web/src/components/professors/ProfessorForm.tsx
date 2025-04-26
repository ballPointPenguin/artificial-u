import type { Component, JSX } from 'solid-js';
import { For, Show, createEffect, createResource, createSignal } from 'solid-js';
import { getDepartments } from '../../api/services/department-service'; // Import department service
import { generateProfessor } from '../../api/services/professor-service'; // Import professor generate service
import type { Department, Professor } from '../../api/types';
import { Button } from '../ui/Button';

// Form data interface matching the API model
export interface ProfessorFormData {
  name: string
  title: string
  description: string
  teaching_style: string
  gender: string
  accent: string
  age: number | null
  department_id: number | null // Add department ID
  specialization?: string
  background?: string
  personality?: string
  image_url?: string
}

interface ProfessorFormProps {
  professor?: Professor
  onSubmit: (data: ProfessorFormData) => Promise<void>
  onCancel: () => void
  isSubmitting: boolean
  error?: string
  setError?: (error: string) => void
}

const ProfessorForm: Component<ProfessorFormProps> = (props) => {
  // State for controlled form inputs
  const [formData, setFormData] = createSignal<ProfessorFormData>({
    name: '',
    title: '',
    description: '',
    teaching_style: '',
    gender: '',
    accent: '',
    age: null,
    department_id: null,
    specialization: '',
    background: '',
    personality: '',
    image_url: '',
  })

  // State for generation
  const [isGenerating, setIsGenerating] = createSignal(false)
  const [generateError, setGenerateError] = createSignal<string | null>(null)

  // Keep formData in sync with props.professor (for edit mode)
  createEffect(() => {
    setFormData({
      name: props.professor?.name || '',
      title: props.professor?.title || '',
      description: props.professor?.description || '',
      teaching_style: props.professor?.teaching_style || '',
      gender: props.professor?.gender || '',
      accent: props.professor?.accent || '',
      age: props.professor?.age || null,
      department_id: props.professor?.department_id || null,
      specialization: props.professor?.specialization || '',
      background: props.professor?.background || '',
      personality: props.professor?.personality || '',
      image_url: props.professor?.image_url || '',
    })
  })

  // Fetch departments for the dropdown
  const [departmentsResource] = createResource(async () => {
    try {
      // Fetch all departments - adjust if pagination is needed later
      const response = await getDepartments()
      return response.items
    } catch (error: unknown) {
      console.error('Failed to fetch departments:', error)
      // Optionally set an error state for the form
      if (props.setError) {
        // Check if error is an instance of Error before accessing message
        const errorMessage = error instanceof Error ? error.message : String(error);
        props.setError(`Failed to load departments: ${errorMessage}`)
      }
      return [] // Return empty array on error
    }
  })

  const handleInput: JSX.EventHandler<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement, InputEvent> = (e) => {
    const { name, value, type } = e.currentTarget;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? null : Number(value)) : type === 'select-one' && value === '' ? null : value,
    }));
  };

  const handleSubmit = (e: SubmitEvent) => {
    e.preventDefault()
    // Now use the signal state instead of FormData
    try {
      void props.onSubmit(formData())
    } catch (error: unknown) {
      if (props.setError) {
        props.setError(error instanceof Error ? error.message : String(error))
      }
    }
  }

  const handleGenerate = async () => {
    setGenerateError(null)
    setIsGenerating(true)

    // Prepare partial attributes (optional)
    const partialAttributes: Record<string, unknown> = {}
    if (formData().accent) partialAttributes.accent = formData().accent
    if (formData().age) partialAttributes.age = formData().age
    if (formData().background) partialAttributes.background = formData().background
    if (formData().description) partialAttributes.description = formData().description
    if (formData().gender) partialAttributes.gender = formData().gender
    if (formData().name) partialAttributes.name = formData().name
    if (formData().personality) partialAttributes.personality = formData().personality
    if (formData().specialization) partialAttributes.specialization = formData().specialization
    if (formData().teaching_style) partialAttributes.teaching_style = formData().teaching_style
    if (formData().title) partialAttributes.title = formData().title

    try {
      const generated = await generateProfessor({
        partial_attributes: Object.keys(partialAttributes).length > 0 ? partialAttributes : undefined,
      })

      // Update form state with generated data, keeping existing ID if editing
      setFormData(prev => ({
        ...prev, // Keep existing fields like ID if they were there
        accent: generated.accent || prev.accent,
        age: generated.age ?? prev.age,
        background: generated.background || prev.background,
        description: generated.description || prev.description,
        gender: generated.gender || prev.gender,
        name: generated.name || prev.name, // Use generated or keep previous
        personality: generated.personality || prev.personality,
        specialization: generated.specialization || prev.specialization,
        teaching_style: generated.teaching_style || prev.teaching_style,
        title: generated.title || prev.title,
        // department_id should likely remain as selected by the user
        // image_url shouldn't be generated here
      }))
    } catch (err: unknown) {
      let message = 'Failed to generate professor profile'
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

  // Helper to disable inputs/buttons during submission or generation
  const isDisabled = () => props.isSubmitting || isGenerating()

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <div>
        <label
          for="name"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Professor Name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          value={formData().name}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <div>
        <label
          for="title"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Title
        </label>
        <input
          id="title"
          name="title"
          type="text"
          value={formData().title}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <div>
        <label
          for="department_id"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Department (Required for Generate)
        </label>
        <select
          id="department_id"
          name="department_id"
          class="arcane-input appearance-none"
          value={formData().department_id ?? ''}
          onInput={handleInput}
          disabled={departmentsResource.loading || isDisabled()}
        >
          <option value="">-- Select Department --</option>
          <Show
            when={!departmentsResource.loading && departmentsResource()}
            fallback={<option disabled>Loading departments...</option>}
          >
            {/* Check if the resource data is an array before mapping */}
            <For each={Array.isArray(departmentsResource()) ? departmentsResource() : []}>{(dept: Department) =>
              <option value={dept.id}>{dept.name} ({dept.code})</option>
            }</For>
          </Show>
        </select>
        {/* Explicitly check if error is truthy */}
        <Show when={!!departmentsResource.error}>
            <p class="mt-1 text-sm text-red-600">Failed to load departments.</p>
        </Show>
      </div>

      <div>
        <label
          for="specialization"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Specialization (Required for Generate)
        </label>
        <input
          id="specialization"
          name="specialization"
          type="text"
          value={formData().specialization || ''}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
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
          rows={3}
          value={formData().description}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <div>
        <label
          for="background"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Background
        </label>
        <textarea
          id="background"
          name="background"
          rows={3}
          value={formData().background || ''}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <div>
        <label
          for="personality"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Personality
        </label>
        <input
          id="personality"
          name="personality"
          type="text"
          value={formData().personality || ''}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <div>
        <label
          for="teaching_style"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Teaching Style
        </label>
        <input
          id="teaching_style"
          name="teaching_style"
          type="text"
          value={formData().teaching_style}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <div>
        <label
          for="gender"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Gender
        </label>
        <input
          id="gender"
          name="gender"
          type="text"
          value={formData().gender}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <div>
        <label
          for="accent"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Accent
        </label>
        <input
          id="accent"
          name="accent"
          type="text"
          value={formData().accent}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <div>
        <label
          for="age"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Age
        </label>
        <input
          id="age"
          name="age"
          type="number"
          value={formData().age ?? ''}
          onInput={handleInput}
          class="arcane-input"
          disabled={isDisabled()}
        />
      </div>

      <Show when={props.error}>
        <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded">
          {props.error}
        </div>
      </Show>
      {/* Show Generation Error */}
      <Show when={generateError()}>
        <div class="bg-yellow-900/20 border border-yellow-500 text-yellow-300 px-4 py-3 rounded">
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
        {/* Generate Button */}
        <Button
          type="button"
          variant="secondary"
          onClick={() => { void handleGenerate() }}
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
                <title>Generate</title> { /* Added title for accessibility */ }
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
            : props.professor !== undefined
              ? 'Update'
              : 'Save'}
        </Button>
      </div>
    </form>
  )
}

export default ProfessorForm
