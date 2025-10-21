import { A } from '@solidjs/router'
import { createEffect, createSignal, For, on, Show } from 'solid-js'
import { topicService } from '../../api/services/topic-service.js'
import type { APIError, Topic, TopicCreate, TopicUpdate } from '../../api/types.js'
import { RequireAuth } from '../../auth/RequireAuth.js'
import { createJobTracker } from '../../utils/job-management.js'
import { Alert } from '../ui/Alert.jsx'
import { Button } from '../ui/Button.jsx'
import { MagicButton } from '../ui/MagicButton.jsx'
import { TopicContentRenderer } from './TopicContentRenderer.jsx'
import { TopicForm } from './TopicForm.jsx'

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
  // Use job tracker for reactive job state management
  const jobTracker = createJobTracker({
    courseId: () => props.courseId,
    kinds: ['generate_topics_for_course'],
    onJobStart: (event) => {
      console.log('Topic generation started:', event.id)
    },
    onJobComplete: (event) => {
      console.log('Topic generation completed:', event.id)
      setListVersion((v) => v + 1)
    },
    onJobFail: (event) => {
      console.error('Topic generation failed:', event.last_error)
      setError({ detail: event.last_error || 'Topic generation failed' })
    },
  })

  const [currentJob, setCurrentJob] = createSignal<{ id: number } | null>(null)

  // Check for existing topic generation jobs on mount
  createEffect(() => {
    if (props.courseId && !jobTracker.isInitializing()) {
      // Look for any running topic generation jobs for this course
      const activeJobIds = Array.from(jobTracker.activeJobIds())
      if (activeJobIds.length > 0) {
        // For simplicity, just track the first active job
        setCurrentJob({ id: activeJobIds[0] })
      }
    }
  })

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
    setError(null) // Clear any previous errors
    try {
      // Enqueue async job instead of direct generation
      const job = await topicService.enqueueGenerateTopicsForCourse(props.courseId, {
        course_id: props.courseId,
      })
      setCurrentJob({ id: job.id })
      console.log('Enqueued topic generation job:', job.id)
    } catch (err) {
      console.error('Failed to enqueue topic generation:', err)
      setError(
        err instanceof Error
          ? { detail: err.message }
          : { detail: 'Failed to enqueue topic generation' }
      )
    }
  }

  return (
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-display text-parchment-100">Course Topics</h2>
        <div class="flex space-x-2">
          <RequireAuth>
            <MagicButton
              type="button"
              onClick={() => {
                void handleGenerateTopics()
              }}
              variant="secondary"
              disabled={jobTracker.hasActiveJobs() || isLoading()}
              isLoading={jobTracker.hasActiveJobs()}
              loadingText="Generating..."
            >
              Generate Topics
            </MagicButton>
            <Button onClick={handleAddTopic} variant="primary" disabled={isLoading()}>
              Add New Topic
            </Button>
          </RequireAuth>
        </div>
      </div>

      <Show when={jobTracker.lastError()}>
        <Alert variant="danger" class="mb-4" title="Topic Generation Failed">
          {jobTracker.lastError()}
        </Alert>
      </Show>
      <Show when={currentJob() && !jobTracker.hasActiveJobs()}>
        <Alert variant="success" class="mb-4">
          Topic generation completed for Job #{currentJob()?.id}
        </Alert>
      </Show>
      <Show when={currentJob() && jobTracker.hasActiveJobs()}>
        <Alert variant="info" class="mb-4">
          Topic generation in progress for Job #{currentJob()?.id}. You can continue browsing; this
          will update when complete.
        </Alert>
      </Show>

      <Show when={showForm()}>
        <RequireAuth>
          <TopicForm
            courseId={props.courseId}
            existingTopic={editingTopic()}
            onSubmit={handleSubmitForm}
            onCancel={handleCancelForm}
            isLoading={isSubmitting()}
            error={formError()}
          />
        </RequireAuth>
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
                  <div class="flex-1">
                    <A
                      href={`/courses/${String(props.courseId)}/topics/${String(topic.id)}`}
                      class="block hover:text-primary transition-colors duration-200"
                    >
                      <h3 class="text-lg font-semibold text-parchment-100">{topic.title}</h3>
                      <p class="text-sm text-parchment-300 font-serif">
                        Week: {topic.week}, Order: {topic.order}
                      </p>
                    </A>
                    <TopicContentRenderer content={topic.content} class="mt-3" />
                  </div>
                </div>
                <div class="flex justify-end space-x-2 pt-3 border-t border-parchment-800/30">
                  <RequireAuth>
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
                  </RequireAuth>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>
    </div>
  )
}
