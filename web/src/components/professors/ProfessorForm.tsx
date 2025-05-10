import type { Component } from 'solid-js'
import { Show, createEffect, createResource, createSignal } from 'solid-js'
import { departmentService } from '../../api/services/department-service.js'
import { professorService } from '../../api/services/professor-service.js'
import type {
  Department,
  Professor,
  ProfessorCreate,
  ProfessorGenerateRequest,
} from '../../api/types.js'

import { Button, Form, FormActions, FormField, Input, MagicButton, Select, Textarea } from '../ui'
import type { SelectOption } from '../ui'

export interface ProfessorFormData {
  name: string
  title: string
  description: string
  teaching_style: string
  gender: string
  accent: string
  age: number | null
  department_id: number | null
  specialization?: string
  background?: string
  personality?: string
  image_url?: string
}

interface ProfessorFormProps {
  professor?: Professor // Professor data for editing
  onSubmit: (data: ProfessorFormData) => Promise<void>
  onCancel: () => void
  isSubmitting: boolean
  error?: string // General form error from parent
  setError?: (error: string) => void // To set errors from parent or async operations
}

const ProfessorForm: Component<ProfessorFormProps> = (props) => {
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
    image_url: '', // Should not be directly edited here, typically set by other means
  })

  const [validationErrors, setValidationErrors] = createSignal<Record<string, string>>({})
  const [isGenerating, setIsGenerating] = createSignal(false)
  const [generateError, setGenerateError] = createSignal<string | null>(null)

  createEffect(() => {
    const p = props.professor
    setFormData({
      name: p?.name || '',
      title: p?.title || '',
      description: p?.description || '',
      teaching_style: p?.teaching_style || '',
      gender: p?.gender || '',
      accent: p?.accent || '',
      age: p?.age ?? null, // Ensure null if undefined
      department_id: p?.department_id ?? null, // Ensure null if undefined
      specialization: p?.specialization || '',
      background: p?.background || '',
      personality: p?.personality || '',
      image_url: p?.image_url || '', // Populate for reference, but not editable field
    })
  })

  const [departmentsResource] = createResource(async () => {
    try {
      const response = await departmentService.listDepartments({ page: 1, size: 100 })
      return response.items.map((dept: Department) => ({
        value: dept.id,
        label: `${dept.name} (${dept.code})`,
      })) as SelectOption[]
    } catch (error: unknown) {
      console.error('Failed to fetch departments:', error)
      if (props.setError) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        props.setError(`Failed to load departments: ${errorMessage}`)
      }
      return []
    }
  })

  const validateField = (
    fieldName: keyof ProfessorFormData,
    value: string | number | null
  ): string => {
    if (fieldName === 'name' && (!value || String(value).trim() === '')) {
      return 'Professor name is required'
    }
    if (fieldName === 'title' && (!value || String(value).trim() === '')) {
      return 'Title is required'
    }
    // Add more specific validations as needed
    return ''
  }

  const handleInputChange = (fieldName: keyof ProfessorFormData, value: string | number | null) => {
    const error = validateField(fieldName, value)
    setValidationErrors((prev) => ({ ...prev, [fieldName]: error }))
    setFormData((prev) => ({ ...prev, [fieldName]: value }))
  }

  const validateForm = (data: ProfessorFormData): boolean => {
    const newErrors: Record<string, string> = {}
    let isValid = true

    if (!data.name || data.name.trim() === '') {
      newErrors.name = 'Professor name is required'
      isValid = false
    }
    if (!data.title || data.title.trim() === '') {
      newErrors.title = 'Title is required'
      isValid = false
    }
    // Department is not strictly required by API for create/update, but might be for generation
    // No validation for department_id here, but could be added if it's a business rule

    // Example: Age must be a positive number if provided
    if (data.age !== null && data.age <= 0) {
      newErrors.age = 'Age must be a positive number.'
      isValid = false
    }

    setValidationErrors(newErrors)
    return isValid
  }

  const handleSubmit = () => {
    // Form component handles event.preventDefault()
    if (validateForm(formData())) {
      // Prepare data, ensuring optional fields are handled correctly for the API
      const submissionData: ProfessorFormData = {
        ...formData(),
        // API expects null for empty optional number fields, or undefined/omitted
        // For string fields, empty string is usually fine, or null if API allows.
        // The types.ts definitions (ProfessorCreate/Update) use `string | null`, etc.
        // so current formData structure should be mostly fine.
        specialization: formData().specialization || undefined, // Send undefined if empty
        background: formData().background || undefined,
        personality: formData().personality || undefined,
        // image_url is not part of this form's direct submission flow
      }
      void props.onSubmit(submissionData)
    }
  }

  const handleGenerate = async () => {
    setGenerateError(null)
    setIsGenerating(true)
    setValidationErrors({}) // Clear validation errors before generating

    const currentData = formData()

    // Construct partial_attributes carefully based on ProfessorGenerateRequest and ProfessorCreate types
    const partialAttributes: ProfessorCreate = {}
    if (currentData.name) partialAttributes.name = currentData.name
    if (currentData.title) partialAttributes.title = currentData.title
    if (currentData.department_id) partialAttributes.department_id = currentData.department_id
    if (currentData.specialization) partialAttributes.specialization = currentData.specialization
    if (currentData.background) partialAttributes.background = currentData.background
    if (currentData.personality) partialAttributes.personality = currentData.personality
    if (currentData.teaching_style) partialAttributes.teaching_style = currentData.teaching_style
    if (currentData.gender) partialAttributes.gender = currentData.gender
    if (currentData.accent) partialAttributes.accent = currentData.accent
    if (currentData.description) partialAttributes.description = currentData.description
    if (currentData.age !== null) partialAttributes.age = currentData.age
    // image_url is not sent for generation

    const payload: ProfessorGenerateRequest = {
      partial_attributes:
        Object.keys(partialAttributes).length > 0
          ? (partialAttributes as Record<string, unknown>)
          : undefined,
    }

    try {
      const generated = await professorService.generateProfessor(payload)
      setFormData((prev) => ({
        ...prev, // Keep existing fields like ID if they were there
        name: generated.name || prev.name,
        title: generated.title || prev.title,
        description: generated.description || prev.description,
        teaching_style: generated.teaching_style || prev.teaching_style,
        gender: generated.gender || prev.gender,
        accent: generated.accent || prev.accent,
        age: generated.age ?? prev.age,
        // department_id usually set by user, not overwritten by generation unless specifically designed for it
        specialization: generated.specialization || prev.specialization,
        background: generated.background || prev.background,
        personality: generated.personality || prev.personality,
        // image_url is not typically part of this generation flow
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

  const handleClear = () => {
    setFormData({
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
    setValidationErrors({})
    setGenerateError(null)
  }

  const isDisabled = () => props.isSubmitting || isGenerating()

  return (
    <Form onSubmit={handleSubmit}>
      <FormField label="Professor Name" name="name" required error={validationErrors().name}>
        <Input
          name="name"
          value={formData().name}
          onChange={(v) => {
            handleInputChange('name', v)
          }}
          disabled={isDisabled()}
          required
        />
      </FormField>

      <FormField label="Title" name="title" required error={validationErrors().title}>
        <Input
          name="title"
          value={formData().title}
          onChange={(v) => {
            handleInputChange('title', v)
          }}
          disabled={isDisabled()}
          required
        />
      </FormField>

      <FormField
        label="Department"
        name="department_id"
        error={validationErrors().department_id}
        helperText="Department affiliation."
      >
        <Select
          name="department_id"
          options={departmentsResource() || []}
          value={formData().department_id}
          onChange={(v) => {
            handleInputChange('department_id', v === '' ? null : Number(v))
          }}
          placeholder="-- Select Department --"
          disabled={departmentsResource.loading || isDisabled()}
          required
        />
      </FormField>

      <FormField
        label="Specialization"
        name="specialization"
        error={validationErrors().specialization}
        helperText="Primary field of expertise."
      >
        <Input
          name="specialization"
          value={formData().specialization || ''}
          onChange={(v) => {
            handleInputChange('specialization', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <FormField label="Description" name="description" error={validationErrors().description}>
        <Textarea
          name="description"
          rows={3}
          value={formData().description}
          onChange={(v) => {
            handleInputChange('description', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <FormField label="Background" name="background" error={validationErrors().background}>
        <Textarea
          name="background"
          rows={3}
          value={formData().background || ''}
          onChange={(v) => {
            handleInputChange('background', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <FormField label="Personality" name="personality" error={validationErrors().personality}>
        <Input
          name="personality"
          value={formData().personality || ''}
          onChange={(v) => {
            handleInputChange('personality', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <FormField
        label="Teaching Style"
        name="teaching_style"
        error={validationErrors().teaching_style}
      >
        <Input
          name="teaching_style"
          value={formData().teaching_style}
          onChange={(v) => {
            handleInputChange('teaching_style', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <FormField label="Gender" name="gender" error={validationErrors().gender}>
          <Input
            name="gender"
            value={formData().gender}
            onChange={(v) => {
              handleInputChange('gender', v)
            }}
            disabled={isDisabled()}
          />
        </FormField>

        <FormField label="Accent" name="accent" error={validationErrors().accent}>
          <Input
            name="accent"
            value={formData().accent}
            onChange={(v) => {
              handleInputChange('accent', v)
            }}
            disabled={isDisabled()}
          />
        </FormField>

        <FormField label="Age" name="age" error={validationErrors().age}>
          <Input
            name="age"
            type="number"
            value={formData().age ?? ''} // Use empty string for input if null
            onChange={(v) => {
              handleInputChange('age', v === '' ? null : Number(v))
            }}
            disabled={isDisabled()}
          />
        </FormField>
      </div>

      <Show when={props.error}>
        <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded my-4">
          {props.error}
        </div>
      </Show>
      <Show when={generateError()}>
        <div class="bg-yellow-900/20 border border-yellow-500 text-yellow-300 px-4 py-3 rounded my-4">
          {generateError()}
        </div>
      </Show>

      <FormActions>
        <Button type="button" variant="outline" onClick={props.onCancel} disabled={isDisabled()}>
          Cancel
        </Button>
        <Button type="button" variant="outline" onClick={handleClear} disabled={isDisabled()}>
          Clear
        </Button>
        <MagicButton
          type="button"
          variant="secondary"
          onClick={() => {
            void handleGenerate()
          }}
          disabled={isDisabled()}
          isLoading={isGenerating()}
          loadingText="Generating..."
        >
          Generate
        </MagicButton>
        <Button type="submit" variant="primary" disabled={isDisabled()}>
          {props.isSubmitting ? 'Saving...' : props.professor !== undefined ? 'Update' : 'Save'}
        </Button>
      </FormActions>
    </Form>
  )
}

export default ProfessorForm
