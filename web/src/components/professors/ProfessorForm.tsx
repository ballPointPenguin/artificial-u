import type { Component } from 'solid-js'
import { createEffect, createResource, createSignal, Show } from 'solid-js'
import { departmentService } from '../../api/services/department-service.js'
import { professorService } from '../../api/services/professor-service.js'
import type {
  Department,
  Professor,
  ProfessorCreate,
  ProfessorGenerateRequest,
} from '../../api/types.js'
import { useContentLanguage, useTranslations } from '../../i18n'
import { waitForJobResult } from '../../utils/job-management.js'
import type { SelectOption } from '../ui'
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
  freeform_prompt?: string
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
  const t = useTranslations()
  const { contentLanguage } = useContentLanguage()
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
    freeform_prompt: '',
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
      freeform_prompt: '',
    })
  })

  const [departmentsResource] = createResource(contentLanguage, async (lang) => {
    try {
      const response = await departmentService.listDepartments({
        page: 1,
        size: 100,
        language: lang,
      })
      return response.items.map(
        (dept: Department): SelectOption => ({
          value: dept.id,
          label: `${dept.name} (${dept.code})`,
        })
      )
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
      return t().professors.form.nameRequired
    }
    if (fieldName === 'title' && (!value || String(value).trim() === '')) {
      return t().professors.form.titleRequired
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
      newErrors.name = t().professors.form.nameRequired
      isValid = false
    }
    if (!data.title || data.title.trim() === '') {
      newErrors.title = t().professors.form.titleRequired
      isValid = false
    }
    // Department is not strictly required by API for create/update, but might be for generation
    // No validation for department_id here, but could be added if it's a business rule

    // Example: Age must be a positive number if provided
    if (data.age !== null && data.age <= 0) {
      newErrors.age = t().professors.form.agePositive
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
      freeform_prompt: currentData.freeform_prompt || undefined,
    }

    try {
      const job = await professorService.enqueueGenerateProfessor(payload)
      const completedJob = await waitForJobResult(job.id)
      const generatedResult = (
        completedJob.result as { generated_professor?: Professor } | undefined
      )?.generated_professor

      if (!generatedResult) {
        throw new Error('Generation job completed without returning professor data')
      }

      setFormData((prev) => ({
        ...prev, // Keep existing fields like ID if they were there
        name: generatedResult.name || prev.name,
        title: generatedResult.title || prev.title,
        description: generatedResult.description || prev.description,
        teaching_style: generatedResult.teaching_style || prev.teaching_style,
        gender: generatedResult.gender || prev.gender,
        accent: generatedResult.accent || prev.accent,
        age: generatedResult.age ?? prev.age,
        // department_id usually set by user, not overwritten by generation unless specifically designed for it
        specialization: generatedResult.specialization || prev.specialization,
        background: generatedResult.background || prev.background,
        personality: generatedResult.personality || prev.personality,
        // image_url is not typically part of this generation flow
      }))
    } catch (err: unknown) {
      let message = t().professors.form.failedToGenerate
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
      freeform_prompt: '',
    })
    setValidationErrors({})
    setGenerateError(null)
  }

  const isDisabled = () => props.isSubmitting || isGenerating()

  return (
    <Form onSubmit={handleSubmit}>
      <FormField
        label={t().professors.form.nameLabel}
        name="name"
        required
        error={validationErrors().name}
      >
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

      <FormField
        label={t().professors.form.titleLabel}
        name="title"
        required
        error={validationErrors().title}
      >
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
        label={t().professors.form.departmentLabel}
        name="department_id"
        error={validationErrors().department_id}
        helperText={t().professors.form.departmentHelper}
      >
        <Select
          name="department_id"
          options={departmentsResource() || []}
          value={formData().department_id}
          onChange={(v) => {
            handleInputChange('department_id', v === '' ? null : Number(v))
          }}
          placeholder={t().professors.form.departmentPlaceholder}
          disabled={departmentsResource.loading || isDisabled()}
          required
        />
      </FormField>

      <FormField
        label={t().professors.form.specializationLabel}
        name="specialization"
        error={validationErrors().specialization}
        helperText={t().professors.form.specializationHelper}
      >
        <Textarea
          name="specialization"
          rows={2}
          value={formData().specialization || ''}
          onChange={(v) => {
            handleInputChange('specialization', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <FormField
        label={t().professors.form.descriptionLabel}
        name="description"
        error={validationErrors().description}
      >
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

      <FormField
        label={t().professors.form.backgroundLabel}
        name="background"
        error={validationErrors().background}
      >
        <Textarea
          name="background"
          rows={6}
          value={formData().background || ''}
          onChange={(v) => {
            handleInputChange('background', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <FormField
        label={t().professors.form.personalityLabel}
        name="personality"
        error={validationErrors().personality}
      >
        <Textarea
          name="personality"
          rows={3}
          value={formData().personality || ''}
          onChange={(v) => {
            handleInputChange('personality', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <FormField
        label={t().professors.form.teachingStyleLabel}
        name="teaching_style"
        error={validationErrors().teaching_style}
      >
        <Textarea
          name="teaching_style"
          rows={3}
          value={formData().teaching_style}
          onChange={(v) => {
            handleInputChange('teaching_style', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <FormField
          label={t().professors.form.genderLabel}
          name="gender"
          error={validationErrors().gender}
        >
          <Input
            name="gender"
            value={formData().gender}
            onChange={(v) => {
              handleInputChange('gender', v)
            }}
            disabled={isDisabled()}
          />
        </FormField>

        <FormField
          label={t().professors.form.accentLabel}
          name="accent"
          error={validationErrors().accent}
        >
          <Input
            name="accent"
            value={formData().accent}
            onChange={(v) => {
              handleInputChange('accent', v)
            }}
            disabled={isDisabled()}
          />
        </FormField>

        <FormField label={t().professors.form.ageLabel} name="age" error={validationErrors().age}>
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

      <FormField
        label={t().professors.form.aiPromptLabel}
        name="freeform_prompt"
        helperText={t().professors.form.aiPromptHelper}
        error={validationErrors().freeform_prompt}
      >
        <Textarea
          name="freeform_prompt"
          rows={9}
          value={formData().freeform_prompt || ''}
          onChange={(v) => {
            handleInputChange('freeform_prompt', v)
          }}
          disabled={isDisabled()}
        />
      </FormField>

      <Show when={props.error}>
        <Alert variant="danger" class="my-4">
          {props.error}
        </Alert>
      </Show>
      <Show when={generateError()}>
        <Alert variant="warning" class="my-4">
          {generateError()}
        </Alert>
      </Show>

      <FormActions>
        <Button type="button" variant="outline" onClick={props.onCancel} disabled={isDisabled()}>
          {t().common.cancel}
        </Button>
        <Button type="button" variant="outline" onClick={handleClear} disabled={isDisabled()}>
          {t().common.clear}
        </Button>
        <MagicButton
          type="button"
          variant="secondary"
          onClick={() => {
            void handleGenerate()
          }}
          disabled={isDisabled()}
          isLoading={isGenerating()}
          loadingText={t().common.generating}
        >
          {t().common.generate}
        </MagicButton>
        <Button type="submit" variant="primary" disabled={isDisabled()}>
          {props.isSubmitting
            ? t().common.saving
            : props.professor !== undefined
              ? t().common.update
              : t().common.save}
        </Button>
      </FormActions>
    </Form>
  )
}

export default ProfessorForm
