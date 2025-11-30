import { createEffect, createResource, createSignal, type JSX, Show } from 'solid-js'
import { departmentService } from '../../api/services/department-service.js'
import { facultyService } from '../../api/services/faculty-service.js'
import type { Department, DepartmentGenerateRequest } from '../../api/types.js'
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
import type { SelectOption } from '../ui/Select'

// Form data interface matching the API model
interface DepartmentFormData {
  name: string
  code: string
  faculty_id: number | null // Faculty ID instead of string
  description: string | null // Changed from string to string | null
}

interface DepartmentFormProps {
  department?: Department
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
    faculty_id: null,
    description: '',
  })

  // Load faculties for the dropdown
  const [faculties] = createResource(() => facultyService.listFaculties())

  // Keep formData in sync with props.department (for edit mode)
  createEffect(() => {
    setFormData({
      name: props.department?.name || '',
      code: props.department?.code || '',
      faculty_id: props.department?.faculty_id || null,
      description: props.department?.description || '',
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

    if (!currentData.faculty_id) {
      newErrors.faculty_id = 'Faculty is required'
    }

    if (!currentData.description || currentData.description.trim() === '') {
      newErrors.description = 'Description is required'
    }

    setValidationErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Unified input handler using onChange from new components
  const handleInputChange = (fieldName: 'name' | 'code' | 'description', value: string) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }))
  }

  const handleSubmit: JSX.EventHandler<HTMLFormElement, SubmitEvent> = () => {
    if (validateForm(formData())) {
      // Construct FormData object from the signal for submission
      const formSubmissionData = new FormData()
      const data = formData()
      formSubmissionData.append('name', data.name)
      formSubmissionData.append('code', data.code)
      if (data.faculty_id !== null) {
        formSubmissionData.append('faculty_id', String(data.faculty_id))
      }
      if (data.description !== null) {
        formSubmissionData.append('description', data.description)
      }
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
        partial_attributes: {
          name: currentData.name || undefined,
          code: currentData.code || undefined,
          faculty_id: currentData.faculty_id ?? undefined,
          description: currentData.description || undefined,
        },
        // Include department ID if editing an existing department
        ...(props.department?.id && { department_id: props.department.id }),
      }
      const generated = await departmentService.generateDepartment(payload)
      setFormData({
        name: generated.name,
        code: generated.code,
        faculty_id: generated.faculty_id || null,
        description: generated.description || '',
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
      faculty_id: null,
      description: '',
    })
    setValidationErrors({})
    setGenerateError(null)
  }

  // Convert faculties to Select options
  const facultyOptions = (): SelectOption[] => {
    const facs = faculties()
    if (!facs) return []
    return facs.items.map((faculty) => ({
      value: faculty.id,
      label: faculty.name,
    }))
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

      <FormField label="Faculty" name="faculty_id" required error={validationErrors().faculty_id}>
        <Show
          when={!faculties.loading}
          fallback={<div class="text-parchment-300">Loading faculties...</div>}
        >
          <Select
            name="faculty_id"
            value={formData().faculty_id}
            onChange={(value) => {
              setFormData((prev) => ({ ...prev, faculty_id: (value as number) || null }))
            }}
            options={facultyOptions()}
            placeholder="Select a faculty"
            disabled={isDisabled()}
            required
          />
        </Show>
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
        <Alert variant="danger" class="my-4">
          {props.error}
        </Alert>
      </Show>
      <Show when={generateError()}>
        <Alert variant="danger" class="my-4">
          {generateError()}
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
