import { type JSX, Show, createEffect, createSignal } from 'solid-js'
import { departmentService } from '../../api/services/department-service.js'
import type { Department, DepartmentGenerateRequest } from '../../api/types.js'
import { Button, Form, FormActions, FormField, Input, MagicButton, Textarea } from '../ui'

// Form data interface matching the API model
interface DepartmentFormData {
  name: string
  code: string
  faculty: string | null // Allow null to match API type, input will use ''
  description: string | null // Changed from string to string | null
}

interface DepartmentFormProps {
  department?: Department & Partial<DepartmentFormData>
  onSubmit: (data: FormData) => void
  onCancel: () => void
  isSubmitting: boolean
  error?: string
}

const DepartmentForm = (props: DepartmentFormProps) => {
  const [validationErrors, setValidationErrors] = createSignal<Record<string, string>>({})
  const [isGenerating, setIsGenerating] = createSignal(false)
  const [generateError, setGenerateError] = createSignal<string | null>(null)
  const [formData, setFormData] = createSignal<DepartmentFormData>({
    name: '',
    code: '',
    faculty: '', // Initialize with empty string for input compatibility
    description: '', // Initialize with empty string for input compatibility
  })

  // Keep formData in sync with props.department (for edit mode)
  createEffect(() => {
    setFormData({
      name: props.department?.name || '',
      code: props.department?.code || '',
      faculty: props.department?.faculty || '', // Default null to empty string for input
      description: props.department?.description || '', // Default null to empty string for input
    })
  })

  const validateForm = (currentData: DepartmentFormData): boolean => {
    const newErrors: Record<string, string> = {}

    if (!currentData.name || currentData.name.trim() === '') {
      newErrors.name = 'Department name is required'
    }

    if (!currentData.code || currentData.code.trim() === '') {
      newErrors.code = 'Department code is required'
    } else if (currentData.code.length < 2 || currentData.code.length > 10) {
      newErrors.code = 'Code must be between 2 and 10 characters'
    }

    if (!currentData.faculty || currentData.faculty.trim() === '') {
      newErrors.faculty = 'Faculty is required'
    }

    if (!currentData.description || currentData.description.trim() === '') {
      newErrors.description = 'Description is required'
    }

    setValidationErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Unified input handler using onChange from new components
  const handleInputChange = (fieldName: keyof DepartmentFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }))
  }

  const handleSubmit: JSX.EventHandler<HTMLFormElement, SubmitEvent> = () => {
    // event.preventDefault() // Form component handles this if onSubmit is provided
    // const form = event.currentTarget // No longer need to get form element directly for FormData

    if (validateForm(formData())) {
      // Construct FormData object from the signal for submission
      const formSubmissionData = new FormData()
      Object.entries(formData()).forEach(([key, value]) => {
        if (value !== null) {
          formSubmissionData.append(key, value as string)
        }
      })
      props.onSubmit(formSubmissionData)
    }
  }

  const handleGenerate = async () => {
    setGenerateError(null)
    setIsGenerating(true)
    setValidationErrors({}) // Clear previous validation errors

    const currentData = formData()
    // Pre-generation validation (optional, but good practice)
    // For example, if 'name' is required for generation:
    // if (!currentData.name || currentData.name.trim() === '') {
    //   setValidationErrors({ name: 'Department name is required to generate details.' });
    //   setIsGenerating(false);
    //   return;
    // }

    try {
      const payload: DepartmentGenerateRequest = {
        name: currentData.name,
        code: currentData.code,
        // Ensure faculty and description are string or undefined for the API
        faculty: currentData.faculty === '' ? undefined : currentData.faculty || undefined,
        description:
          currentData.description === '' ? undefined : currentData.description || undefined,
      }
      const generated = await departmentService.generateDepartment(payload)
      setFormData({
        name: generated.name,
        code: generated.code,
        faculty: generated.faculty || '', // Ensure input gets a string
        description: generated.description || '', // Ensure input gets a string
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
    <Form onSubmit={handleSubmit}>
      <FormField label="Department Name" name="name" required error={validationErrors().name}>
        <Input
          name="name"
          value={formData().name}
          onChange={(value) => {
            handleInputChange('name', value)
          }}
          disabled={isDisabled()}
          required
        />
      </FormField>

      <FormField
        label="Department Code"
        name="code"
        required
        error={validationErrors().code}
        helperText="Must be between 2 and 10 characters."
      >
        <Input
          name="code"
          value={formData().code}
          onChange={(value) => {
            handleInputChange('code', value)
          }}
          disabled={isDisabled()}
          required
        />
      </FormField>

      <FormField label="Faculty" name="faculty" required error={validationErrors().faculty}>
        <Input
          name="faculty"
          value={formData().faculty || ''}
          onChange={(value) => {
            handleInputChange('faculty', value)
          }}
          disabled={isDisabled()}
          required
        />
      </FormField>

      <FormField
        label="Description"
        name="description"
        required
        error={validationErrors().description}
      >
        <Textarea
          name="description"
          rows={4}
          value={formData().description || ''}
          onChange={(value) => {
            handleInputChange('description', value)
          }}
          disabled={isDisabled()}
          required
        />
      </FormField>

      <Show when={props.error}>
        <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded my-4">
          {props.error}
        </div>
      </Show>
      <Show when={generateError()}>
        <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded my-4">
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
          {props.isSubmitting ? 'Saving...' : props.department !== undefined ? 'Update' : 'Save'}
        </Button>
      </FormActions>
    </Form>
  )
}

export default DepartmentForm
