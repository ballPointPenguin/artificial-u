import { A, useParams } from '@solidjs/router'
import { Show, createResource, createSignal } from 'solid-js'
import { topicService } from '../api/services/topic-service.js'
import { courseService } from '../api/services/course-service.js'
import { lectureService } from '../api/services/lecture-service.js'
import type { TopicUpdate } from '../api/types.js'
import { TopicForm } from '../components/topics/TopicForm.jsx'
import { TopicContentRenderer } from '../components/topics/TopicContentRenderer.jsx'
import { Button, Alert, LoadingSpinner } from '../components/ui'

const TopicDetail = () => {
  const params = useParams()

  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')
  const [lectureError, setLectureError] = createSignal('')
  const [isCreatingLecture, setIsCreatingLecture] = createSignal(false)
  const [isGeneratingLecture, setIsGeneratingLecture] = createSignal(false)
  const [generationTimeout, setGenerationTimeout] = createSignal(false)

  // Parse IDs from URL params
  const courseId = Number.parseInt(params.courseId, 10)
  const topicId = Number.parseInt(params.topicId, 10)

  const isValidIds = !Number.isNaN(courseId) && !Number.isNaN(topicId)

  // Fetch topic and course data
  const [topic] = createResource(() => (isValidIds ? topicId : null), topicService.getTopic)

  const [course] = createResource(() => (isValidIds ? courseId : null), courseService.getCourse)

  // Fetch lecture for this topic
  const [lecture] = createResource(
    () => (isValidIds ? { courseId, topicId } : null),
    async ({ courseId, topicId }) => {
      try {
        const response = await lectureService.listLectures({
          page: 1,
          size: 1,
          courseId,
          topicId,
        })
        return response.items.length > 0 ? response.items[0] : null
      } catch (error) {
        console.error('Failed to fetch lecture:', error)
        return null
      }
    }
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

  const handleCreateLecture = async () => {
    if (!isValidIds) return

    setIsCreatingLecture(true)
    setLectureError('')

    try {
      const newLecture = await lectureService.createLecture({
        course_id: courseId,
        topic_id: topicId,
        title: `Lecture for ${topic()?.title || 'Topic'}`,
        content: '',
      })

      // Navigate to the new lecture
      window.location.href = `/courses/${String(courseId)}/lectures/${String(newLecture.id)}`
    } catch (error) {
      setLectureError(error instanceof Error ? error.message : 'Failed to create lecture')
    } finally {
      setIsCreatingLecture(false)
    }
  }

  const handleGenerateLecture = async () => {
    if (!isValidIds) return

    setIsGeneratingLecture(true)
    setLectureError('')
    setGenerationTimeout(false)

    try {
      const newLecture = await lectureService.generateLecture(
        {
          partial_attributes: {
            course_id: courseId,
            topic_id: topicId,
          },
        },
        () => {
          setGenerationTimeout(true)
          setLectureError('Generation timed out. Please try again.')
        }
      )

      // Navigate to the generated lecture
      window.location.href = `/courses/${String(courseId)}/lectures/${String(newLecture.id)}`
    } catch (error) {
      setLectureError(error instanceof Error ? error.message : 'Failed to generate lecture')
    } finally {
      setIsGeneratingLecture(false)
    }
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

                      {/* Lecture Section */}
                      <div class="border-t border-parchment-800/30 pt-6 mt-6">
                        <h3 class="text-lg font-semibold text-parchment-200 mb-4">Lecture</h3>

                        <Show when={lectureError()}>
                          <Alert variant="danger" class="mb-4">
                            {lectureError()}
                          </Alert>
                        </Show>

                        <Show when={lecture()}>
                          {(lectureData) => (
                            <div class="space-y-4">
                              <div class="flex justify-between items-center">
                                <div>
                                  <h4 class="text-md font-medium text-parchment-300">
                                    {lectureData().title}
                                  </h4>
                                  <p class="text-sm text-parchment-400">
                                    Revision {lectureData().revision}
                                  </p>
                                </div>
                                <div class="flex space-x-2">
                                  <A
                                    href={`/courses/${String(courseId)}/lectures/${String(lectureData().id)}`}
                                    class="inline-block"
                                  >
                                    <Button variant="outline" size="sm">
                                      View Lecture
                                    </Button>
                                  </A>
                                  <A
                                    href={`/courses/${String(courseId)}/lectures/${String(lectureData().id)}`}
                                    class="inline-block"
                                  >
                                    <Button variant="primary" size="sm">
                                      Edit Lecture
                                    </Button>
                                  </A>
                                </div>
                              </div>
                            </div>
                          )}
                        </Show>

                        <Show when={!lecture()}>
                          <div class="text-center py-6">
                            <p class="text-parchment-400 font-serif mb-4">
                              No lecture has been created for this topic yet.
                            </p>
                            <div class="flex justify-center space-x-4">
                              <Button
                                variant="outline"
                                onClick={() => {
                                  void handleCreateLecture()
                                }}
                                disabled={isCreatingLecture()}
                              >
                                {isCreatingLecture() ? 'Creating...' : 'Create Lecture'}
                              </Button>
                              <Button
                                variant="primary"
                                onClick={() => {
                                  void handleGenerateLecture()
                                }}
                                disabled={isGeneratingLecture()}
                              >
                                {isGeneratingLecture() ? 'Generating...' : 'Generate Lecture'}
                              </Button>
                            </div>
                          </div>
                        </Show>

                        {/* Progress indicator for generation */}
                        <Show when={isGeneratingLecture()}>
                          <div class="mt-4 p-4 bg-mystic-900/30 border border-mystic-700 rounded-lg">
                            <div class="flex items-center justify-center space-x-3">
                              <LoadingSpinner />
                              <span class="text-sm text-parchment-300">Generating lecture...</span>
                            </div>
                            <p class="text-xs text-parchment-400 mt-3 text-center">
                              This may take several minutes. Please don't close this page.
                            </p>
                          </div>
                        </Show>

                        {/* Timeout message */}
                        <Show when={generationTimeout()}>
                          <Alert variant="warning" class="mt-4">
                            <p class="text-sm">
                              The generation request took longer than expected and timed out. This
                              can happen with complex content generation. Please try again.
                            </p>
                          </Alert>
                        </Show>
                      </div>
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
