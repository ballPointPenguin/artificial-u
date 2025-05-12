import type { Component } from 'solid-js'
import { Show, createEffect, createResource, createSignal } from 'solid-js'
import { courseService } from '../../api/services/course-service.js'
import { departmentService } from '../../api/services/department-service.js'
import { professorService } from '../../api/services/professor-service.js'
import type { Course, CourseGenerateRequest, Department, Professor } from '../../api/types.js'
import {
  Alert,
  Button,
  Form,
  FormActions,
  FormField,
  Input,
  MagicButton,
  Select,
  Textarea,
} from '../ui'
import type { SelectOption } from '../ui/Select.js'
import type { CourseFormData } from './types.js'

interface CourseFormProps {
  course?: Course // For editing
  onSubmit: (data: CourseFormData) => Promise<void>
  onCancel: () => void
  isSubmitting: boolean
  error?: string
  setError?: (error: string) => void
}

const CourseForm: Component<CourseFormProps> = (props) => {
  const [formData, setFormData] = createSignal<CourseFormData>({
    code: '',
    title: '',
    department_id: null,
    level: '',
    credits: null,
    professor_id: null,
    description: '',
    lectures_per_week: null,
    total_weeks: null,
    generate_prompt: '',
  })

  const [validationErrors, setValidationErrors] = createSignal<Record<string, string>>({})
  const [isGenerating, setIsGenerating] = createSignal(false)
  const [generateError, setGenerateError] = createSignal<string | null>(null)

  // Populate form for editing
  createEffect(() => {
    const c = props.course
    if (c) {
      setFormData({
        code: c.code || '',
        title: c.title || '',
        department_id: c.department_id,
        level: c.level || '',
        credits: c.credits,
        professor_id: c.professor_id,
        description: c.description || '',
        lectures_per_week: c.lectures_per_week,
        total_weeks: c.total_weeks,
        generate_prompt: '', // Reset generate prompt on edit
      })
    }
  })

  // Fetch departments for Select
  const [departmentsResource] = createResource(async () => {
    try {
      const response = await departmentService.listDepartments({ page: 1, size: 100 })
      return response.items.map((dept: Department) => ({
        value: dept.id,
        label: `${dept.name} (${dept.code})`,
      })) as SelectOption[]
    } catch {
      props.setError?.('Failed to load departments')
      return []
    }
  })

  // Fetch professors for Select
  const [professorsResource] = createResource(async () => {
    try {
      const response = await professorService.listProfessors({ page: 1, size: 100 })
      return response.items.map((prof: Professor) => ({
        value: prof.id,
        label: prof.name || 'Unnamed Professor',
      })) as SelectOption[]
    } catch {
      props.setError?.('Failed to load professors')
      return []
    }
  })

  const handleInputChange = (fieldName: keyof CourseFormData, value: string | number | null) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }))

    // When input changes, clear the specific validation error for that field
    if (validationErrors()[fieldName]) {
      setValidationErrors((prev) => {
        const newErrors: Record<string, string> = {}
        for (const key in prev) {
          if (key !== fieldName) {
            newErrors[key] = prev[key]
          }
        }
        return newErrors
      })
    }
  }

  const validateForm = (data: CourseFormData): boolean => {
    const errors: Record<string, string> = {}
    if (!data.code.trim()) errors.code = 'Course code is required.'
    if (!data.title.trim()) errors.title = 'Course title is required.'
    if (data.department_id === null) errors.department_id = 'Department is required.'
    if (data.professor_id === null) errors.professor_id = 'Professor is required.'
    if (!data.level.trim()) errors.level = 'Course level is required.'
    if (data.credits === null || Number(data.credits) <= 0)
      errors.credits = 'Credits must be a positive number.'
    if (!data.description.trim()) errors.description = 'Description is required.'
    // Optional fields like lectures_per_week, total_weeks can be validated if they have specific rules when provided
    if (data.lectures_per_week !== null && Number(data.lectures_per_week) <= 0) {
      errors.lectures_per_week = 'Lectures per week must be a positive number if specified.'
    }
    if (data.total_weeks !== null && Number(data.total_weeks) <= 0) {
      errors.total_weeks = 'Total weeks must be a positive number if specified.'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = () => {
    if (validateForm(formData())) {
      void props.onSubmit(formData()) // Parent will handle mapping to Create/Update payload
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    setGenerateError(null)
    setValidationErrors({}) // Clear validation before generation

    const currentData = formData()
    const payload: CourseGenerateRequest = {
      partial_attributes: {
        // Only include fields that have values, to guide generation
        ...(currentData.code && { code: currentData.code }),
        ...(currentData.title && { title: currentData.title }),
        ...(currentData.department_id && { department_id: currentData.department_id }),
        ...(currentData.professor_id && { professor_id: currentData.professor_id }),
        ...(currentData.level && { level: currentData.level }),
        // Let credits, description etc. be generated if not filled
      },
      ...(currentData.generate_prompt && { freeform_prompt: currentData.generate_prompt }),
    }

    // Remove partial_attributes if it's empty
    if (payload.partial_attributes && Object.keys(payload.partial_attributes).length === 0) {
      delete payload.partial_attributes
    }

    try {
      const generated = await courseService.generateCourse(payload)
      setFormData((prev) => ({
        ...prev,
        code: generated.code || prev.code,
        title: generated.title || prev.title,
        department_id: generated.department_id,
        level: generated.level || prev.level,
        credits: generated.credits,
        professor_id: generated.professor_id,
        description: generated.description || prev.description,
        lectures_per_week: generated.lectures_per_week,
        total_weeks: generated.total_weeks,
      }))
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : 'Failed to generate course details')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleClear = () => {
    setFormData({
      code: '',
      title: '',
      department_id: null,
      level: '',
      credits: null,
      professor_id: null,
      description: '',
      lectures_per_week: null,
      total_weeks: null,
      generate_prompt: '',
    })
    setValidationErrors({})
    setGenerateError(null)
  }

  const isDisabled = () => props.isSubmitting || isGenerating()

  return (
    <Form onSubmit={handleSubmit}>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        <FormField label="Course Code" name="code" required error={validationErrors().code}>
          <Input
            name="code"
            value={formData().code}
            onChange={(v) => {
              handleInputChange('code', v)
            }}
            disabled={isDisabled()}
            required
          />
        </FormField>
        <FormField label="Course Title" name="title" required error={validationErrors().title}>
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
          required
          error={validationErrors().department_id}
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
          label="Professor"
          name="professor_id"
          required
          error={validationErrors().professor_id}
        >
          <Select
            name="professor_id"
            options={professorsResource() || []}
            value={formData().professor_id}
            onChange={(v) => {
              handleInputChange('professor_id', v === '' ? null : Number(v))
            }}
            placeholder="-- Select Professor --"
            disabled={professorsResource.loading || isDisabled()}
            required
          />
        </FormField>
        <FormField label="Course Level" name="level" required error={validationErrors().level}>
          <Input
            name="level"
            value={formData().level}
            onChange={(v) => {
              handleInputChange('level', v)
            }}
            placeholder="e.g., Undergraduate 101, Graduate 505"
            disabled={isDisabled()}
            required
          />
        </FormField>
        <FormField label="Credits" name="credits" required error={validationErrors().credits}>
          <Input
            name="credits"
            type="number"
            value={formData().credits ?? ''}
            onChange={(v) => {
              handleInputChange('credits', v === '' ? null : Number(v))
            }}
            disabled={isDisabled()}
            required
          />
        </FormField>
        <FormField
          label="Lectures per Week (Optional)"
          name="lectures_per_week"
          error={validationErrors().lectures_per_week}
        >
          <Input
            name="lectures_per_week"
            type="number"
            value={formData().lectures_per_week ?? ''}
            onChange={(v) => {
              handleInputChange('lectures_per_week', v === '' ? null : Number(v))
            }}
            disabled={isDisabled()}
          />
        </FormField>
        <FormField
          label="Total Weeks (Optional)"
          name="total_weeks"
          error={validationErrors().total_weeks}
        >
          <Input
            name="total_weeks"
            type="number"
            value={formData().total_weeks ?? ''}
            onChange={(v) => {
              handleInputChange('total_weeks', v === '' ? null : Number(v))
            }}
            disabled={isDisabled()}
          />
        </FormField>
      </div>

      <FormField
        label="Description"
        name="description"
        required
        error={validationErrors().description}
      >
        <Textarea
          name="description"
          rows={4}
          value={formData().description}
          onChange={(v) => {
            handleInputChange('description', v)
          }}
          disabled={isDisabled()}
          required
        />
      </FormField>

      <FormField
        label="AI Generation Prompt (Optional)"
        name="generate_prompt"
        helperText="Provide a freeform prompt to guide AI generation for topics, detailed description, etc."
        error={validationErrors().generate_prompt}
      >
        <Textarea
          name="generate_prompt"
          rows={3}
          value={formData().generate_prompt || ''}
          onChange={(v) => {
            handleInputChange('generate_prompt', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      {/* Display errors */}
      <Show when={props.error || generateError()}>
        <Alert variant="danger" class="my-4">
          {props.error || generateError()}
        </Alert>
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
          Generate Details
        </MagicButton>
        <Button type="submit" variant="primary" disabled={isDisabled()}>
          {props.isSubmitting
            ? 'Saving...'
            : props.course !== undefined
              ? 'Update Course'
              : 'Save Course'}
        </Button>
      </FormActions>
    </Form>
  )
}

export default CourseForm
