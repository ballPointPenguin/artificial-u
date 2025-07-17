import { createSignal, onMount, Show } from 'solid-js'
import type { APIError, Topic, TopicContent, TopicCreate, TopicUpdate } from '../../api/types.js'
import { Button } from '../ui/Button.jsx'
import FormField from '../ui/FormField.jsx'
import Input from '../ui/Input.jsx'
import Textarea from '../ui/Textarea.jsx'

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
  const [content, setContent] = createSignal('')
  const [contentError, setContentError] = createSignal<string | null>(null)

  onMount(() => {
    if (props.existingTopic) {
      setTitle(props.existingTopic.title)
      setWeek(props.existingTopic.week.toString())
      setOrder(props.existingTopic.order.toString())
      // Convert existing content to JSON string for editing
      if (props.existingTopic.content) {
        setContent(JSON.stringify(props.existingTopic.content, null, 2))
      } else {
        setContent('')
      }
    } else {
      // Reset for new topic form
      setTitle('')
      setWeek('') // Default week or let user input
      setOrder('') // Default order or let user input
      setContent('')
    }
  })

  const validateContent = (contentStr: string): boolean => {
    if (!contentStr.trim()) {
      setContentError(null)
      return true
    }

    try {
      JSON.parse(contentStr)
      setContentError(null)
      return true
    } catch {
      setContentError('Invalid JSON format')
      return false
    }
  }

  const handleSubmit = async (e: SubmitEvent) => {
    e.preventDefault()
    const parsedWeek = parseInt(week(), 10)
    const parsedOrder = parseInt(order(), 10)

    if (isNaN(parsedWeek) || isNaN(parsedOrder)) {
      console.error('Week and Order must be valid numbers.')
      return
    }

    // Validate content JSON if provided
    if (!validateContent(content())) {
      return
    }

    // Parse content JSON if provided
    let parsedContent: TopicContent = null
    if (content().trim()) {
      try {
        parsedContent = JSON.parse(content())
      } catch (error) {
        console.error('Invalid JSON in content field:', error)
        return
      }
    }

    const topicData = {
      title: title(),
      week: parsedWeek,
      order: parsedOrder,
      content: parsedContent,
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
      class="arcane-card p-6 space-y-4"
    >
      <h3 class="text-xl font-display text-parchment-100 mb-4">
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

      <FormField name="topicContent" label="Content (JSON)">
        <Textarea
          name="topicContent"
          value={content()}
          onInput={(e: Event & { currentTarget: HTMLTextAreaElement }) => {
            const newContent = e.currentTarget.value
            setContent(newContent)
            validateContent(newContent)
          }}
          placeholder='{"lecture": "Topic description", "readings": ["Reading 1", "Reading 2"], "objectives": ["Objective 1", "Objective 2"]}'
          rows={8}
          error={contentError()}
        />
        <p class="text-xs text-parchment-400 mt-1">
          Enter JSON content for the topic. Example: lecture text, readings array, objectives array, etc.
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
