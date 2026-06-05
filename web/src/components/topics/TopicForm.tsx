import { createEffect, createSignal, Show } from 'solid-js'
import { topicService } from '../../api/services/topic-service.js'
import type {
  APIError,
  Topic,
  TopicContent,
  TopicCreate,
  TopicDraft,
  TopicGenerateSingleRequest,
  TopicUpdate,
} from '../../api/types.js'
import { useTranslations } from '../../i18n'
import { Alert } from '../ui/Alert.jsx'
import { Button } from '../ui/Button.jsx'
import FormField from '../ui/FormField.jsx'
import Input from '../ui/Input.jsx'
import { MagicButton } from '../ui/MagicButton.jsx'
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
  const t = useTranslations()
  const [title, setTitle] = createSignal('')
  const [week, setWeek] = createSignal('')
  const [order, setOrder] = createSignal('')
  const [content, setContent] = createSignal('')
  const [freeformPrompt, setFreeformPrompt] = createSignal('')
  const [contentError, setContentError] = createSignal<string | null>(null)
  const [generateError, setGenerateError] = createSignal<string | null>(null)
  const [isGenerating, setIsGenerating] = createSignal(false)

  const resetForm = (mode: 'existing' | 'blank') => {
    if (mode === 'existing' && props.existingTopic) {
      setTitle(props.existingTopic.title)
      setWeek(props.existingTopic.week.toString())
      setOrder(props.existingTopic.order.toString())
      if (props.existingTopic.content) {
        setContent(JSON.stringify(props.existingTopic.content, null, 2))
      } else {
        setContent('')
      }
    } else {
      setTitle('')
      setWeek('')
      setOrder('')
      setContent('')
    }
    setFreeformPrompt('')
    setContentError(null)
    setGenerateError(null)
  }

  createEffect(() => {
    if (props.existingTopic) {
      resetForm('existing')
    } else {
      resetForm('blank')
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
      setContentError(t().topicDetail.form.invalidJsonError)
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
        parsedContent = JSON.parse(content()) as TopicContent
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
      })
    } else {
      await props.onSubmit({ ...topicData, course_id: props.courseId })
    }
  }

  const handleGenerate = async () => {
    setGenerateError(null)

    const parsedWeek = parseInt(week(), 10)
    const parsedOrder = parseInt(order(), 10)

    if (isNaN(parsedWeek) || isNaN(parsedOrder)) {
      setGenerateError(t().topicDetail.form.weekOrderRequired)
      return
    }

    setIsGenerating(true)
    try {
      const payload: TopicGenerateSingleRequest = {
        week: parsedWeek,
        order: parsedOrder,
        freeform_prompt: freeformPrompt().trim() || undefined,
      }
      const generated: TopicDraft = await topicService.generateSingleTopicForCourse(
        props.courseId,
        payload
      )
      setTitle(generated.title)
      setWeek(generated.week.toString())
      setOrder(generated.order.toString())
      setContent(generated.content ? JSON.stringify(generated.content, null, 2) : '')
      setContentError(null)
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : t().topicDetail.form.failedToGenerate)
    } finally {
      setIsGenerating(false)
    }
  }

  const isDisabled = () => Boolean(props.isLoading) || isGenerating()

  return (
    <form
      onSubmit={(e) => {
        void handleSubmit(e)
      }}
      class="arcane-card p-6 space-y-4"
    >
      <h3 class="text-xl font-display text-parchment-100 mb-4">
        {props.existingTopic
          ? t().topicDetail.form.editHeading
          : t().topicDetail.form.createHeading}
      </h3>

      <FormField name="topicTitle" label={t().topicDetail.form.titleLabel} required>
        <Input
          name="topicTitle"
          type="text"
          value={title()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setTitle(e.currentTarget.value)
          }
          placeholder={t().topicDetail.form.titlePlaceholder}
          required
        />
      </FormField>

      <FormField name="topicWeek" label={t().topicDetail.form.weekLabel} required>
        <Input
          name="topicWeek"
          type="number"
          value={week()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setWeek(e.currentTarget.value)
          }
          placeholder={t().topicDetail.form.weekPlaceholder}
          required
          min="1"
        />
      </FormField>

      <FormField name="topicOrder" label={t().topicDetail.form.orderLabel} required>
        <Input
          name="topicOrder"
          type="number"
          value={order()}
          onInput={(e: Event & { currentTarget: HTMLInputElement }) =>
            setOrder(e.currentTarget.value)
          }
          placeholder={t().topicDetail.form.orderPlaceholder}
          required
          min="1"
        />
      </FormField>

      <FormField name="topicContent" label={t().topicDetail.form.contentLabel}>
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
        <p class="text-xs text-parchment-400 mt-1">{t().topicDetail.form.contentHelper}</p>
      </FormField>

      <FormField
        name="topicFreeformPrompt"
        label={t().topicDetail.form.aiPromptLabel}
        helperText={t().topicDetail.form.aiPromptHelper}
      >
        <Textarea
          name="topicFreeformPrompt"
          value={freeformPrompt()}
          onInput={(e: Event & { currentTarget: HTMLTextAreaElement }) =>
            setFreeformPrompt(e.currentTarget.value)
          }
          placeholder="Example: emphasize neuroplasticity in stroke rehabilitation, include clinical case studies."
          rows={6}
          disabled={isDisabled()}
        />
      </FormField>

      <Show when={props.error}>
        <Alert variant="danger" class="my-2">
          {props.error?.detail}
        </Alert>
      </Show>

      <Show when={generateError()}>
        <Alert variant="warning" class="my-2">
          {generateError()}
        </Alert>
      </Show>

      <div class="flex justify-end space-x-3 pt-3 mt-4 border-t border-parchment-800/30">
        <Button type="button" variant="outline" onClick={props.onCancel} disabled={isDisabled()}>
          {t().common.cancel}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            resetForm('blank')
          }}
          disabled={isDisabled()}
        >
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
          {props.isLoading
            ? t().common.saving
            : props.existingTopic
              ? t().topicDetail.form.updateLabel
              : t().topicDetail.form.createLabel}
        </Button>
      </div>
    </form>
  )
}
