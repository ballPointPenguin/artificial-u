import { type Component, Show, createMemo, createSignal } from 'solid-js'
import { generateCourse } from '../../api/services/course-service'
import type { Course } from '../../api/types'
import { Button, MagicButton } from '../ui'
import { BasicInfo } from './BasicInfo'
import { Description } from './Description'
import { CourseFormProvider, useCourseForm } from './FormContext'
import { Topics } from './Topics'
import { type CourseFormData, type FormProps, defaultFormData } from './types'

// Internal component that uses the context
function CourseFormContent(props: {
  onSubmit: (data: CourseFormData) => void | Promise<void>
  isSubmitting: boolean
  error: string
  onCancel: () => void
  course?: Course
}) {
  const { form, validateForm, updateForm, resetTopics } = useCourseForm()
  const [isGenerating, setIsGenerating] = createSignal(false)
  const [generateError, setGenerateError] = createSignal<string | null>(null)

  const handleSubmit = (e: Event) => {
    e.preventDefault()
    if (validateForm()) {
      void props.onSubmit(form)
    }
  }

  const handleGenerate = async () => {
    setGenerateError(null)
    setIsGenerating(true)

    // Prepare partial attributes
    const partialAttributes: Record<string, unknown> = {}
    if (form.code) partialAttributes.code = form.code
    if (form.title) partialAttributes.title = form.title
    if (form.department_id) partialAttributes.department_id = form.department_id
    if (form.level) partialAttributes.level = form.level
    if (form.credits) partialAttributes.credits = form.credits
    if (form.professor_id) partialAttributes.professor_id = form.professor_id
    if (form.description) partialAttributes.description = form.description
    if (form.lectures_per_week) partialAttributes.lectures_per_week = form.lectures_per_week
    if (form.total_weeks) partialAttributes.total_weeks = form.total_weeks
    partialAttributes.topics = form.topics

    try {
      const generated = await generateCourse({
        partial_attributes:
          Object.keys(partialAttributes).length > 0 ? partialAttributes : undefined,
      })

      // Update form with generated data
      if (generated.code) updateForm('code', generated.code)
      if (generated.title) updateForm('title', generated.title)
      if (generated.level) updateForm('level', generated.level)
      if (generated.credits) updateForm('credits', generated.credits)
      if (generated.description) updateForm('description', generated.description)
      if (generated.lectures_per_week) updateForm('lectures_per_week', generated.lectures_per_week)
      if (generated.total_weeks) updateForm('total_weeks', generated.total_weeks)

      // Update topics if they exist - special handling needed for arrays
      if (generated.topics && Array.isArray(generated.topics)) {
        // Replace the entire topics array to ensure reactivity
        resetTopics(generated.topics)
      }
    } catch (err: unknown) {
      let message = 'Failed to generate course'
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

  const isDisabled = () => props.isSubmitting || isGenerating()

  return (
    <form onSubmit={handleSubmit} class="space-y-4">
      <BasicInfo disabled={isDisabled()} />
      <Description disabled={isDisabled()} />
      <Topics disabled={isDisabled()} />

      <Show when={props.error}>
        <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded">
          {props.error}
        </div>
      </Show>
      <Show when={generateError()}>
        <div class="bg-yellow-900/20 border border-yellow-500 text-yellow-300 px-4 py-3 rounded">
          {generateError()}
        </div>
      </Show>

      <div class="flex justify-end space-x-3">
        <Button type="button" variant="outline" onClick={props.onCancel} disabled={isDisabled()}>
          Cancel
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

// Main container component that provides the context
const CourseForm: Component<FormProps> = (props) => {
  // Initialize with course data or defaults
  const initialFormData = createMemo(() => {
    if (props.course) {
      const course = props.course
      const topics = Array.isArray(course.topics)
        ? course.topics.map((t) => ({
            week_number: Number(t.week_number),
            order_in_week: Number(t.order_in_week),
            title: String(t.title),
          }))
        : Array.from({ length: course.total_weeks ?? 14 }, (_, i) => ({
            week_number: i + 1,
            order_in_week: 1,
            title: '',
          }))

      return {
        code: course.code || '',
        title: course.title || '',
        department_id: course.department_id || null,
        level: course.level || 'Undergraduate',
        credits: course.credits || 3,
        professor_id: course.professor_id || null,
        description: course.description || '',
        lectures_per_week: course.lectures_per_week || 1,
        total_weeks: course.total_weeks || 14,
        topics,
      }
    }
    return defaultFormData
  })

  return (
    <CourseFormProvider initialData={initialFormData()}>
      <CourseFormContent
        onSubmit={props.onSubmit}
        isSubmitting={props.isSubmitting}
        error={props.error}
        onCancel={props.onCancel}
        course={props.course}
      />
    </CourseFormProvider>
  )
}

export default CourseForm
