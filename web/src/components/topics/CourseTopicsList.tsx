import { For, Show, createSignal, createEffect, on } from 'solid-js'
import { topicService } from '../../api/services/topic-service.js'
import type { Topic, TopicCreate, TopicUpdate, APIError } from '../../api/types.js'
import { Button } from '../ui/Button.jsx'
import { TopicForm } from './TopicForm.jsx'
import { Alert } from '../ui/Alert.jsx'
import { MagicButton } from '../ui/MagicButton.jsx'

interface CourseTopicsListProps {
  courseId: number
}

export function CourseTopicsList(props: CourseTopicsListProps) {
  const [topics, setTopics] = createSignal<Topic[]>([])
  const [isLoading, setIsLoading] = createSignal(false)
  const [error, setError] = createSignal<APIError | null>(null)
  const [listVersion, setListVersion] = createSignal(0)

  const [showForm, setShowForm] = createSignal(false)
  const [editingTopic, setEditingTopic] = createSignal<Topic | null>(null)
  const [formError, setFormError] = createSignal<APIError | null>(null)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [generationError, setGenerationError] = createSignal<APIError | null>(null)
  const [isGenerating, setIsGenerating] = createSignal(false)

  createEffect(
    on(
      [() => props.courseId, listVersion],
      ([courseId]) => {
        if (courseId) {
          setIsLoading(true)
          setError(null)
          topicService
            .listTopicsByCourse(courseId, 1, 100)
            .then((response) => {
              const sortedTopics = response.items.sort((a, b) => {
                if (a.week !== b.week) return a.week - b.week
                return a.order - b.order
              })
              setTopics(sortedTopics)
            })
            .catch((err: unknown) => {
              console.error('Failed to fetch topics:', err)
              setError(
                err instanceof Error
                  ? { detail: err.message }
                  : { detail: 'Unknown error fetching topics' }
              )
            })
            .finally(() => setIsLoading(false))
        }
      },
      { defer: false }
    )
  )

  const handleAddTopic = () => {
    setEditingTopic(null)
    setFormError(null)
    setShowForm(true)
  }

  const handleEditTopic = (topic: Topic) => {
    setEditingTopic(topic)
    setFormError(null)
    setShowForm(true)
  }

  const handleCancelForm = () => {
    setShowForm(false)
    setEditingTopic(null)
    setFormError(null)
  }

  const handleSubmitForm = async (data: TopicCreate | TopicUpdate) => {
    setIsSubmitting(true)
    setFormError(null)
    try {
      const currentEditingTopic = editingTopic()
      if (currentEditingTopic) {
        await topicService.updateTopic(currentEditingTopic.id, data as TopicUpdate)
      } else {
        await topicService.createTopic(data as TopicCreate)
      }
      setShowForm(false)
      setEditingTopic(null)
      setListVersion((v) => v + 1)
    } catch (err) {
      console.error('Failed to save topic:', err)
      setFormError(
        err instanceof Error ? { detail: err.message } : { detail: 'Failed to save topic' }
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteTopic = async (topicId: number) => {
    if (confirm('Are you sure you want to delete this topic?')) {
      setIsLoading(true)
      try {
        await topicService.deleteTopic(topicId)
        setListVersion((v) => v + 1)
      } catch (err) {
        console.error('Failed to delete topic:', err)
        setError(
          err instanceof Error ? { detail: err.message } : { detail: 'Failed to delete topic' }
        )
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handleGenerateTopics = async () => {
    setIsGenerating(true)
    setGenerationError(null)
    try {
      const generatedTopics = await topicService.generateTopicsForCourse(props.courseId, {
        course_id: props.courseId,
      })
      if (generatedTopics.length > 0) {
        setListVersion((v) => v + 1)
      } else {
        console.info('Topic generation resulted in no new topics or an empty list.')
      }
    } catch (err) {
      console.error('Failed to generate topics:', err)
      setGenerationError(
        err instanceof Error ? { detail: err.message } : { detail: 'Failed to generate topics' }
      )
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-display text-parchment-100">Course Topics</h2>
        <div class="flex space-x-2">
          <MagicButton
            type="button"
            onClick={() => {
              void handleGenerateTopics()
            }}
            variant="secondary"
            disabled={isGenerating() || isLoading()}
            isLoading={isGenerating()}
            loadingText="Generating..."
          >
            Generate Topics
          </MagicButton>
          <Button onClick={handleAddTopic} variant="primary" disabled={isLoading()}>
            Add New Topic
          </Button>
        </div>
      </div>

      <Show when={generationError()}>
        <Alert variant="danger" class="mb-4" title="Topic Generation Failed">
          {generationError()?.detail}
        </Alert>
      </Show>

      <Show when={showForm()}>
        <TopicForm
          courseId={props.courseId}
          existingTopic={editingTopic()}
          onSubmit={handleSubmitForm}
          onCancel={handleCancelForm}
          isLoading={isSubmitting()}
          error={formError()}
        />
      </Show>

      <Show when={isLoading() && topics().length === 0 && !showForm()}>
        <p class="text-parchment-400 font-serif text-center py-10">Loading topics...</p>
      </Show>

      <Show when={error() && !showForm()}>
        <Alert variant="danger" title="Error Fetching Topics">
          {error()?.detail}
        </Alert>
      </Show>

      <Show when={!isLoading() && topics().length === 0 && !error() && !showForm()}>
        <div class="arcane-card p-6 text-center">
          <p class="text-parchment-400 font-serif mb-2">No topics found for this course.</p>
          <p class="text-sm text-parchment-300 font-serif mb-4">
            You can add topics manually or try generating them with AI.
          </p>
        </div>
      </Show>

      <Show when={topics().length > 0 && !showForm()}>
        <div class="space-y-4">
          <For each={topics()}>
            {(topic) => (
              <div class="arcane-card p-4 hover:shadow-md transition-shadow duration-200">
                <div class="flex justify-between items-start mb-3">
                  <div>
                    <h3 class="text-lg font-semibold text-parchment-100">{topic.title}</h3>
                    <p class="text-sm text-parchment-300 font-serif">
                      Week: {topic.week}, Order: {topic.order}
                    </p>
                  </div>
                </div>
                <div class="flex justify-end space-x-2 pt-3 border-t border-parchment-800/30">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      handleEditTopic(topic)
                    }}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    class="text-danger-foreground border-danger-border hover:bg-danger-bg/20 hover:text-danger-foreground"
                    onClick={() => {
                      void handleDeleteTopic(topic.id)
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>
    </div>
  )
}
