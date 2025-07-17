import { A, useParams } from '@solidjs/router'
import { Show, createResource, createSignal } from 'solid-js'
import { topicService } from '../api/services/topic-service.js'
import { courseService } from '../api/services/course-service.js'
import type { TopicUpdate } from '../api/types.js'
import { TopicForm } from '../components/topics/TopicForm.jsx'
import { TopicContentRenderer } from '../components/topics/TopicContentRenderer.jsx'
import { Button, Alert } from '../components/ui'

const TopicDetail = () => {
  const params = useParams()

  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')

  // Parse IDs from URL params
  const courseId = Number.parseInt(params.courseId, 10)
  const topicId = Number.parseInt(params.topicId, 10)

  const isValidIds = !Number.isNaN(courseId) && !Number.isNaN(topicId)

  // Fetch topic and course data
  const [topic] = createResource(
    () => (isValidIds ? topicId : null),
    topicService.getTopic
  )

  const [course] = createResource(
    () => (isValidIds ? courseId : null),
    courseService.getCourse
  )

  const handleSubmitUpdate = async (formData: TopicUpdate) => {
    if (!isValidIds) return

    setIsSubmitting(true)
    setError('')

    try {
      await topicService.updateTopic(topicId, formData)
      setIsEditing(false)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update topic')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setError('')
  }



  return (
    <div class="container mx-auto px-4 py-8">
      <Show when={isValidIds} fallback={<div class="text-parchment-100">Invalid Topic ID.</div>}>
        <Show
          when={!topic.loading}
          fallback={<div class="text-center py-8 text-parchment-300">Loading topic...</div>}
        >
          <Show
            when={!topic.error}
            fallback={
              <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded">
                Error: {topic.error instanceof Error ? topic.error.message : 'Failed to load topic'}
              </div>
            }
          >
            <Show when={topic()} keyed>
              {(topicData) => (
                <div>
                  {/* Breadcrumb navigation */}
                  <div class="mb-6">
                    <A
                      href={`/courses/${String(courseId)}`}
                      class="text-mystic-500 hover:text-mystic-300"
                    >
                      ← Back to Course
                    </A>
                  </div>

                  {/* Course context */}
                  <Show when={course()}>
                    {(courseData) => (
                      <div class="mb-6">
                        <h2 class="text-lg text-parchment-300">
                          {courseData().code}: {courseData().title}
                        </h2>
                      </div>
                    )}
                  </Show>

                  {/* Error Display */}
                  <Show when={error()}>
                    <Alert variant="danger" class="mb-4">
                      {error()}
                    </Alert>
                  </Show>

                  <Show
                    when={!isEditing()}
                    fallback={
                      <TopicForm
                        courseId={courseId}
                        existingTopic={topicData}
                        onSubmit={handleSubmitUpdate}
                        onCancel={handleCancelEdit}
                        isLoading={isSubmitting()}
                        error={error() ? { detail: error() } : null}
                      />
                    }
                  >
                    {/* Topic Detail View */}
                    <div class="arcane-card">
                      <div class="flex justify-between items-start mb-6">
                        <div>
                          <h1 class="text-3xl font-display text-parchment-100 mb-2">
                            {topicData.title}
                          </h1>
                          <p class="text-parchment-300">
                            Week {topicData.week} • Order {topicData.order}
                          </p>
                        </div>
                        <Button variant="primary" onClick={() => setIsEditing(true)}>
                          Edit Topic
                        </Button>
                      </div>

                      {/* Topic Content */}
                      <Show when={topicData.content}>
                        <div class="border-t border-parchment-800/30 pt-6">
                          <TopicContentRenderer content={topicData.content} />
                        </div>
                      </Show>

                      <Show when={!topicData.content}>
                        <div class="border-t border-parchment-800/30 pt-6">
                          <p class="text-parchment-400 font-serif italic">
                            No content defined for this topic.
                          </p>
                        </div>
                      </Show>
                    </div>
                  </Show>
                </div>
              )}
            </Show>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default TopicDetail