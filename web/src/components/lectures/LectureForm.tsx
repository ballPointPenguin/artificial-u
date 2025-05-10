import { createSignal, Show, onMount } from 'solid-js'
import type { Lecture, LectureCreate, LectureUpdate, APIError } from '../../api/types.js'
import { Button } from '../ui/Button.jsx'
import Input from '../ui/Input.jsx'
import Textarea from '../ui/Textarea.jsx'
import FormField from '../ui/FormField.jsx'

interface LectureFormProps {
  courseId: number
  existingLecture?: Lecture | null
  onSubmit: (data: LectureCreate | LectureUpdate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
  error?: APIError | null
}

export function LectureForm(props: LectureFormProps) {
  const [topicId, setTopicId] = createSignal('')
  const [content, setContent] = createSignal('')
  const [summary, setSummary] = createSignal('')
  const [revision, setRevision] = createSignal('1')

  onMount(() => {
    if (props.existingLecture) {
      setTopicId(props.existingLecture.topic_id.toString())
      setContent(props.existingLecture.content)
      setSummary(props.existingLecture.summary || '')
      setRevision(props.existingLecture.revision.toString())
    } else {
      setTopicId('')
      setContent('')
      setSummary('')
      setRevision('1')
    }
  })

  const handleSubmit = async (e: SubmitEvent) => {
    e.preventDefault()
    const parsedTopicId = parseInt(topicId(), 10)
    const parsedRevision = parseInt(revision(), 10)

    const commonData = {
      topic_id: isNaN(parsedTopicId) ? undefined : parsedTopicId,
      content: content(),
      summary: summary() || null,
      revision: isNaN(parsedRevision) ? 1 : parsedRevision,
    }

    if (props.existingLecture) {
      await props.onSubmit({
        ...commonData,
        course_id: props.existingLecture.course_id,
      } as LectureUpdate)
    } else {
      if (commonData.topic_id === undefined) {
        console.error('Topic ID is required and must be a valid number.')
        return
      }
      await props.onSubmit({
        ...commonData,
        course_id: props.courseId,
        topic_id: commonData.topic_id,
      } as LectureCreate)
    }
  }

  return (
    <form
      onSubmit={(e) => {
        void handleSubmit(e)
      }}
      class="space-y-6 p-6 bg-surface rounded-lg shadow-lg border border-border/20"
    >
      <h2 class="text-xl font-display text-primary mb-6">
        {props.existingLecture ? 'Edit Lecture' : 'Create New Lecture'}
      </h2>

      <FormField name="topicId" label="Topic ID" required>
        <Input
          name="topicId"
          type="number"
          value={topicId()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setTopicId(e.currentTarget.value)
          }
          placeholder="Enter Topic ID (e.g., 123)"
          required
        />
      </FormField>

      <FormField name="content" label="Content" required>
        <Textarea
          name="content"
          value={content()}
          onInput={(e: Event & { currentTarget: HTMLTextAreaElement }) =>
            setContent(e.currentTarget.value)
          }
          placeholder="Enter lecture content (Markdown supported)"
          required
          rows={10}
          class="min-h-[150px]"
        />
      </FormField>

      <FormField name="summary" label="Summary (Optional)">
        <Textarea
          name="summary"
          value={summary()}
          onInput={(e: Event & { currentTarget: HTMLTextAreaElement }) =>
            setSummary(e.currentTarget.value)
          }
          placeholder="Enter a brief summary of the lecture"
          rows={4}
          class="min-h-[80px]"
        />
      </FormField>

      <FormField name="revision" label="Revision" required>
        <Input
          name="revision"
          type="number"
          value={revision()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setRevision(e.currentTarget.value)
          }
          placeholder="Revision number (e.g., 1)"
          min="1"
          required
        />
      </FormField>

      <Show when={props.error}>
        <div
          class="p-3 my-2 text-sm text-danger-foreground bg-danger-bg border border-danger-border rounded-md"
          role="alert"
        >
          <span class="font-medium">Error:</span> {props.error?.detail}
        </div>
      </Show>

      <div class="flex justify-end space-x-3 pt-4 border-t border-border/20 mt-6">
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
