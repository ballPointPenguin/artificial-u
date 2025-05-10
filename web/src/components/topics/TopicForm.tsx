import { createSignal, Show, onMount } from 'solid-js'
import type { Topic, TopicCreate, TopicUpdate, APIError } from '../../api/types.js'
import { Button } from '../ui/Button.jsx'
import Input from '../ui/Input.jsx'
import FormField from '../ui/FormField.jsx'

interface TopicFormProps {
  courseId: number // Needed for creating a new topic
  existingTopic?: Topic | null
  onSubmit: (data: TopicCreate | TopicUpdate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
  error?: APIError | null
}

export function TopicForm(props: TopicFormProps) {
  const [title, setTitle] = createSignal('')
  const [week, setWeek] = createSignal('')
  const [order, setOrder] = createSignal('')

  onMount(() => {
    if (props.existingTopic) {
      setTitle(props.existingTopic.title)
      setWeek(props.existingTopic.week.toString())
      setOrder(props.existingTopic.order.toString())
    } else {
      // Reset for new topic form
      setTitle('')
      setWeek('') // Default week or let user input
      setOrder('') // Default order or let user input
    }
  })

  const handleSubmit = async (e: SubmitEvent) => {
    e.preventDefault()
    const parsedWeek = parseInt(week(), 10)
    const parsedOrder = parseInt(order(), 10)

    if (isNaN(parsedWeek) || isNaN(parsedOrder)) {
      // Handle error: week and order must be valid numbers
      // This could be a local error signal displayed in the form
      console.error('Week and Order must be valid numbers.')
      // props.setError({ detail: 'Week and Order must be valid numbers.' }) // If form has local error display
      return
    }

    const topicData = {
      title: title(),
      week: parsedWeek,
      order: parsedOrder,
    }

    if (props.existingTopic) {
      await props.onSubmit({
        ...topicData,
        course_id: props.existingTopic.course_id,
      } as TopicUpdate)
    } else {
      await props.onSubmit({ ...topicData, course_id: props.courseId } as TopicCreate)
    }
  }

  return (
    <form
      onSubmit={(e) => {
        void handleSubmit(e)
      }}
      class="space-y-4 p-6 bg-surface rounded-lg shadow-md border border-border/20"
    >
      <h3 class="text-lg font-semibold text-foreground mb-4">
        {props.existingTopic ? 'Edit Topic' : 'Create New Topic'}
      </h3>

      <FormField name="topicTitle" label="Title" required>
        <Input
          name="topicTitle"
          type="text"
          value={title()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setTitle(e.currentTarget.value)
          }
          placeholder="Enter topic title"
          required
        />
      </FormField>

      <FormField name="topicWeek" label="Week Number" required>
        <Input
          name="topicWeek"
          type="number"
          value={week()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setWeek(e.currentTarget.value)
          }
          placeholder="Enter week number"
          required
          min="1"
        />
      </FormField>

      <FormField name="topicOrder" label="Order in Week" required>
        <Input
          name="topicOrder"
          type="number"
          value={order()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setOrder(e.currentTarget.value)
          }
          placeholder="Enter order within the week"
          required
          min="1"
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

      <div class="flex justify-end space-x-3 pt-3 mt-4 border-t border-border/20">
        <Button type="button" variant="outline" onClick={props.onCancel} disabled={props.isLoading}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" disabled={props.isLoading}>
          {props.isLoading
            ? props.existingTopic
              ? 'Saving...'
              : 'Creating...'
            : props.existingTopic
              ? 'Save Changes'
              : 'Create Topic'}
        </Button>
      </div>
    </form>
  )
}
