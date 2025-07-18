import { createSignal, onMount, Show } from 'solid-js'
import type { APIError, Lecture, LectureCreate, LectureUpdate } from '../../api/types.js'
import { Button } from '../ui/Button.jsx'
import FormField from '../ui/FormField.jsx'
import Input from '../ui/Input.jsx'
import Textarea from '../ui/Textarea.jsx'

interface LectureFormProps {
  courseId: number
  topicId?: number
  existingLecture?: Lecture | null
  onSubmit: (data: LectureCreate | LectureUpdate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
  error?: APIError | null
}

export function LectureForm(props: LectureFormProps) {
  const [title, setTitle] = createSignal('')
  const [content, setContent] = createSignal('')

  onMount(() => {
    if (props.existingLecture) {
      setTitle(props.existingLecture.title)
      setContent(props.existingLecture.content)
    } else {
      // Reset for new lecture form
      setTitle('')
      setContent('')
    }
  })

  const handleSubmit = async (e: SubmitEvent) => {
    e.preventDefault()

    const lectureData = {
      title: title(),
      content: content(),
    }

    if (props.existingLecture) {
      await props.onSubmit(lectureData as LectureUpdate)
    } else {
      if (!props.topicId) {
        throw new Error('topicId is required for creating a new lecture')
      }
      await props.onSubmit({
        ...lectureData,
        course_id: props.courseId,
        topic_id: props.topicId,
      } as LectureCreate)
    }
  }

  return (
    <form
      onSubmit={(e) => {
        void handleSubmit(e)
      }}
      class="arcane-card p-6 space-y-4"
    >
      <h3 class="text-xl font-display text-parchment-100 mb-4">
        {props.existingLecture ? 'Edit Lecture' : 'Create New Lecture'}
      </h3>

      <FormField name="lectureTitle" label="Title" required>
        <Input
          name="lectureTitle"
          type="text"
          value={title()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setTitle(e.currentTarget.value)
          }
          placeholder="Enter lecture title"
          required
        />
      </FormField>

      <FormField name="lectureContent" label="Content" required>
        <Textarea
          name="lectureContent"
          value={content()}
          onInput={(e: Event & { currentTarget: HTMLTextAreaElement }) =>
            setContent(e.currentTarget.value)
          }
          placeholder="Enter lecture content..."
          rows={12}
          required
        />
        <p class="text-xs text-parchment-400 mt-1">
          Enter the lecture content. This will be the main text of the lecture.
        </p>
      </FormField>

      <Show when={props.error}>
        <div
          class="p-3 my-2 text-sm text-danger-foreground bg-danger-bg border border-danger-border rounded-md"
          role="alert"
        >
          <span class="font-medium">Error:</span> {props.error?.detail}
        </div>
      </Show>

      <div class="flex justify-end space-x-3 pt-3 mt-4 border-t border-parchment-800/30">
        <Button type="button" variant="outline" onClick={props.onCancel} disabled={props.isLoading}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" disabled={props.isLoading}>
          {props.isLoading
            ? props.existingLecture
              ? 'Saving...'
              : 'Creating...'
            : props.existingLecture
              ? 'Save Changes'
              : 'Create Lecture'}
        </Button>
      </div>
    </form>
  )
}
