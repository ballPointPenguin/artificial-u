import { Show } from 'solid-js'
import type { Component } from 'solid-js'
import type { Professor } from '../../api/types'
import { Button } from '../ui/Button'

// Form data interface matching the API model
export interface ProfessorFormData {
  name: string
  title: string
  description: string
  teaching_style: string
  gender: string
  accent: string
  age: number | null
  voice_id?: number
  department_id?: string
  specialization?: string
  background?: string
  personality?: string
  image_path?: string
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
  const handleSubmit = (e: SubmitEvent) => {
    e.preventDefault()
    const form = e.currentTarget as HTMLFormElement
    const formData = new FormData(form)

    const data: ProfessorFormData = {
      name: formData.get('name') as string,
      title: formData.get('title') as string,
      description: formData.get('description') as string,
      teaching_style: formData.get('teaching_style') as string,
      gender: formData.get('gender') as string,
      accent: formData.get('accent') as string,
      age: Number.parseInt(formData.get('age') as string) || null,
      specialization: (formData.get('specialization') as string) || undefined,
      background: (formData.get('background') as string) || undefined,
      personality: (formData.get('personality') as string) || undefined,
      image_path: (formData.get('image_path') as string) || undefined,
    }

    try {
      void props.onSubmit(data)
    } catch (error: unknown) {
      if (props.setError) {
        props.setError(error instanceof Error ? error.message : String(error))
      }
    }
  }

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
          value={props.professor?.name || ''}
          class="arcane-input"
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
          value={props.professor?.title || ''}
          class="arcane-input"
        />
      </div>

      <div>
        <label
          for="specialization"
          class="block text-sm font-medium mb-1 text-parchment-300"
        >
          Specialization
        </label>
        <input
          id="specialization"
          name="specialization"
          type="text"
          value={props.professor?.specialization || ''}
          class="arcane-input"
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
          value={props.professor?.description || ''}
          class="arcane-input"
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
          value={props.professor?.background || ''}
          class="arcane-input"
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
          value={props.professor?.personality || ''}
          class="arcane-input"
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
          value={props.professor?.teaching_style || ''}
          class="arcane-input"
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
          value={props.professor?.gender || ''}
          class="arcane-input"
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
          value={props.professor?.accent || ''}
          class="arcane-input"
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
          value={props.professor?.age || ''}
          class="arcane-input"
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
            : props.professor !== undefined
              ? 'Update Professor'
              : 'Create Professor'}
        </Button>
      </div>
    </form>
  )
}

export default ProfessorForm
