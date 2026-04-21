import { A } from '@solidjs/router'
import { createEffect, createSignal, For, on, Show } from 'solid-js'
import { topicService } from '../../api/services/topic-service.js'
import type { APIError, Topic, TopicCreate, TopicUpdate } from '../../api/types.js'
import { useAuth } from '../../auth/AuthProvider.js'
import { RequireRole } from '../../auth/RequireRole.js'
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
  const auth = useAuth()
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

  // Batch generation handlers (admin only)
  const [batchJobMessage, setBatchJobMessage] = createSignal<string | null>(null)

  const handleGenerateRemainingLectures = async (topicId: number) => {
    if (
      !confirm('This will generate lectures for this topic and all subsequent topics. Continue?')
    ) {
      return
    }

    try {
      const result = await topicService.generateRemainingLectures(topicId)
      setBatchJobMessage(result.message || 'Batch generation started')
      console.log('Started batch lecture generation:', result)
      // Refresh the list to show job status
      setTimeout(() => {
        setListVersion((v) => v + 1)
        setBatchJobMessage(null)
      }, 3000)
    } catch (err) {
      console.error('Failed to start batch generation:', err)
      setError(
        err instanceof Error
          ? { detail: err.message }
          : { detail: 'Failed to start batch generation' }
      )
    }
  }

  const handleRegenerateRemainingAudio = async (topicId: number) => {
    if (
      !confirm('This will regenerate audio for all lectures from this topic forward. Continue?')
    ) {
      return
    }

    try {
      const result = await topicService.regenerateRemainingAudio(topicId)
      setBatchJobMessage(result.message || 'Batch audio regeneration started')
      console.log('Started batch audio regeneration:', result)
      setTimeout(() => {
        setBatchJobMessage(null)
      }, 3000)
    } catch (err) {
      console.error('Failed to start batch audio regeneration:', err)
      setError(
        err instanceof Error
          ? { detail: err.message }
          : { detail: 'Failed to start batch audio regeneration' }
      )
    }
  }

  const handleRegenerateRemainingLectures = async (topicId: number) => {
    if (
      !confirm(
        'This will OVERWRITE all lectures (content + audio) from this topic forward. Continue?'
      )
    ) {
      return
    }

    try {
      const result = await topicService.regenerateRemainingLectures(topicId)
      setBatchJobMessage(result.message || 'Batch lecture regeneration started')
      console.log('Started batch lecture regeneration:', result)
      setTimeout(() => {
        setListVersion((v) => v + 1)
        setBatchJobMessage(null)
      }, 3000)
    } catch (err) {
      console.error('Failed to start batch lecture regeneration:', err)
      setError(
        err instanceof Error
          ? { detail: err.message }
          : { detail: 'Failed to start batch lecture regeneration' }
      )
    }
  }

  const handleGenerateRemainingTimelines = async (topicId: number) => {
    if (
      !confirm(
        'This will (re)generate timelines for all lectures with audio from this topic forward. Continue?'
      )
    ) {
      return
    }

    try {
      const result = await topicService.generateRemainingTimelines(topicId)
      setBatchJobMessage(result.message || 'Batch timeline generation started')
      console.log('Started batch timeline generation:', result)
      setTimeout(() => {
        setBatchJobMessage(null)
      }, 3000)
    } catch (err) {
      console.error('Failed to start batch timeline generation:', err)
      setError(
        err instanceof Error
          ? { detail: err.message }
          : { detail: 'Failed to start batch timeline generation' }
      )
    }
  }

  return (
    <div class="space-y-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <h2 class="text-2xl font-display text-parchment-100">Course Topics</h2>
        <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:justify-end">
          <RequireRole minRole="creator">
            <MagicButton
              type="button"
              onClick={() => {
                void handleGenerateTopics()
              }}
              variant="secondary"
              disabled={jobTracker.hasActiveJobs() || isLoading()}
              isLoading={jobTracker.hasActiveJobs()}
              loadingText="Generating..."
              class="w-full sm:w-auto"
            >
              Generate Topics
            </MagicButton>
            <Button
              onClick={handleAddTopic}
              variant="primary"
              disabled={isLoading()}
              class="w-full sm:w-auto"
            >
              Add New Topic
            </Button>
          </RequireRole>
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
      <Show when={batchJobMessage()}>
        <Alert variant="success" class="mb-4">
          {batchJobMessage()}
        </Alert>
      </Show>

      <Show when={showForm()}>
        <RequireRole minRole="creator">
          <TopicForm
            courseId={props.courseId}
            existingTopic={editingTopic()}
            onSubmit={handleSubmitForm}
            onCancel={handleCancelForm}
            isLoading={isSubmitting()}
            error={formError()}
          />
        </RequireRole>
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
                <div class="flex flex-col gap-2 pt-3 border-t border-parchment-800/30">
                  <div class="flex justify-end space-x-2">
                    <Show when={auth.canModify(topic.created_by)}>
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
                    </Show>
                  </div>
                  <RequireRole minRole="admin">
                    <div class="flex flex-wrap justify-end gap-2 pt-2 border-t border-mystic-800/20">
                      <p class="w-full text-xs text-parchment-400 text-right mb-1">
                        Admin: Batch Operations
                      </p>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          void handleGenerateRemainingLectures(topic.id)
                        }}
                        title="Generate lectures for this topic and all subsequent topics"
                      >
                        Generate Remaining Lectures
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          void handleRegenerateRemainingAudio(topic.id)
                        }}
                        title="Regenerate audio for existing lectures from this topic forward"
                      >
                        Regenerate Remaining Audio
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          void handleGenerateRemainingTimelines(topic.id)
                        }}
                        title="(Re)generate forced-alignment timelines for lectures with audio from this topic forward"
                      >
                        Generate Remaining Timelines
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          void handleRegenerateRemainingLectures(topic.id)
                        }}
                        title="Fully regenerate all lectures (content + audio) from this topic forward"
                        class="text-warning-foreground border-warning-border hover:bg-warning-bg/20"
                      >
                        Regenerate Remaining Lectures
                      </Button>
                    </div>
                  </RequireRole>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>
    </div>
  )
}
