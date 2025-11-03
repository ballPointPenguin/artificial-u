import { A, useParams } from '@solidjs/router'
import { createMemo, createResource, createSignal, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { lectureService } from '../api/services/lecture-service.js'
import { topicService } from '../api/services/topic-service.js'
import type { TopicUpdate } from '../api/types.js'
import { RequireRole } from '../auth/RequireRole'
import { LectureSection } from '../components/lectures/LectureSection.jsx'
import { TopicContentRenderer } from '../components/topics/TopicContentRenderer.jsx'
import { TopicForm } from '../components/topics/TopicForm.jsx'
import { Alert, Button } from '../components/ui'
import { createJobTracker, getJobMessage } from '../utils/job-management.js'

const TopicDetail = () => {
  const params = useParams()

  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')
  const [lectureError, setLectureError] = createSignal('')
  const [isGeneratingLecture, setIsGeneratingLecture] = createSignal(false)
  const [generationTimeout, setGenerationTimeout] = createSignal(false)

  // Parse IDs from URL params
  const courseId = createMemo(() => Number.parseInt(params.courseId, 10))
  const topicId = createMemo(() => Number.parseInt(params.topicId, 10))

  const isValidIds = createMemo(() => !Number.isNaN(courseId()) && !Number.isNaN(topicId()))

  // Fetch topic and course data
  const [topic] = createResource(() => (isValidIds() ? topicId() : null), topicService.getTopic)

  const [course] = createResource(() => (isValidIds() ? courseId() : null), courseService.getCourse)

  // Fetch topics for this course to enable prev/next navigation
  const [topicsList] = createResource(
    () => (isValidIds() ? courseId() : null),
    (cid) => topicService.listTopicsByCourse(cid, 1, 100)
  )

  const compareTopics = (
    a: { week: number; order: number; id: number },
    b: {
      week: number
      order: number
      id: number
    }
  ) => {
    if (a.week !== b.week) return a.week - b.week
    if (a.order !== b.order) return a.order - b.order
    return a.id - b.id
  }

  // Fetch lecture for this topic
  const [lecture, { refetch: refetchLecture }] = createResource(
    () => (isValidIds() ? { courseId: courseId(), topicId: topicId() } : null),
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

  // Track jobs for this topic - pass reactive accessor
  const jobTracker = createJobTracker({
    topicId: () => (isValidIds() ? topicId() : undefined),
    kinds: ['generate_lecture', 'generate_lecture_audio', 'generate_lecture_summary'],
    onJobComplete: (event) => {
      if (import.meta.env.DEV) {
        console.log('[TopicDetail] Job completed:', event.kind, event.id)
      }

      if (event.kind === 'generate_lecture') {
        setGenerationTimeout(false)
        setIsGeneratingLecture(false)

        // Refresh lecture data when generation completes
        // Use setTimeout to ensure state updates happen after SSE processing
        setTimeout(() => {
          void refetchLecture()
        }, 100)
      } else if (
        event.kind === 'generate_lecture_audio' ||
        event.kind === 'generate_lecture_summary'
      ) {
        // Also refresh for audio/summary completion
        setTimeout(() => {
          void refetchLecture()
        }, 100)
      }
    },
    onJobFail: (event) => {
      if (import.meta.env.DEV) {
        console.log('[TopicDetail] Job failed:', event.kind, event.id)
      }

      if (event.kind === 'generate_lecture') {
        setIsGeneratingLecture(false)
        setLectureError(getJobMessage(event.kind, 'failed'))
      }
    },
    onJobStart: (event) => {
      if (import.meta.env.DEV) {
        console.log('[TopicDetail] Job started:', event.kind, event.id, event.status)
      }

      // Job start events logged but no UI message needed
      // The Jobs bar handles status display
    },
  })

  const handleSubmitUpdate = async (formData: TopicUpdate) => {
    if (!isValidIds()) return

    setIsSubmitting(true)
    setError('')

    try {
      await topicService.updateTopic(topicId(), formData)
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

  const handleLectureDeleted = () => {
    // Refresh the lecture data after deletion
    void refetchLecture()
  }

  const handleLectureUpdated = () => {
    // Refresh lecture after actions like audio generation
    void refetchLecture()
  }

  const handleGenerateLecture = async () => {
    if (!isValidIds()) return

    setIsGeneratingLecture(true)
    setLectureError('')
    setGenerationTimeout(false)

    try {
      // Prevent duplicate enqueue if a job is already active for this topic
      if (jobTracker.hasActiveJobs()) {
        setIsGeneratingLecture(false)
        return
      }

      const job = await lectureService.enqueueGenerateLecture({
        partial_attributes: {
          course_id: courseId(),
          topic_id: topicId(),
        },
      })

      if (import.meta.env.DEV) {
        console.log('[TopicDetail] Enqueued lecture generation job:', job.id)
      }

      // Note: Don't set isGeneratingLecture to false here - wait for job completion
      // The jobTracker will handle clearing it when the job completes
    } catch (error) {
      setLectureError(error instanceof Error ? error.message : 'Failed to generate lecture')
      setIsGeneratingLecture(false)
    }
  }

  return (
    <div class="container mx-auto px-4 py-8">
      <Show when={isValidIds()} fallback={<div class="text-parchment-100">Invalid Topic ID.</div>}>
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
                      href={`/courses/${String(courseId())}`}
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

                  {/* Prev/Next Topic navigation */}
                  <Show when={topicsList() && topic()}>
                    {(() => {
                      const list = topicsList()
                      const curTopic = topic()
                      const items = list ? list.items.slice().sort(compareTopics) : []
                      const currentIndex = curTopic
                        ? items.findIndex((t) => t.id === curTopic.id)
                        : -1
                      const prev = currentIndex > 0 ? items[currentIndex - 1] : null
                      const next =
                        currentIndex >= 0 && currentIndex < items.length - 1
                          ? items[currentIndex + 1]
                          : null
                      return (
                        <div class="mb-4 flex items-center justify-between gap-3">
                          <div>
                            <Show when={prev}>
                              {(p) => {
                                const prevId = p().id
                                return (
                                  <A
                                    href={`/courses/${String(courseId())}/topics/${String(prevId)}`}
                                    class="text-mystic-500 hover:text-mystic-300"
                                  >
                                    ← Previous Topic
                                  </A>
                                )
                              }}
                            </Show>
                          </div>
                          <div>
                            <Show when={next}>
                              {(n) => {
                                const nextId = n().id
                                return (
                                  <A
                                    href={`/courses/${String(courseId())}/topics/${String(nextId)}`}
                                    class="text-mystic-500 hover:text-mystic-300"
                                  >
                                    Next Topic →
                                  </A>
                                )
                              }}
                            </Show>
                          </div>
                        </div>
                      )
                    })()}
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
                      <RequireRole minRole="creator">
                        <TopicForm
                          courseId={courseId()}
                          existingTopic={topicData}
                          onSubmit={handleSubmitUpdate}
                          onCancel={handleCancelEdit}
                          isLoading={isSubmitting()}
                          error={error() ? { detail: error() } : null}
                        />
                      </RequireRole>
                    }
                  >
                    {/* Two-column layout for larger screens */}
                    <div class="lg:grid lg:grid-cols-2 lg:gap-6">
                      {/* Topic content - takes full width on mobile, left column on desktop */}
                      <div class="lg:col-span-1">
                        {/* Topic Detail View */}
                        <div class="arcane-card">
                          <div class="flex justify-between items-start mb-6">
                            <div class="pr-2">
                              <h1 class="text-3xl font-display text-parchment-100 mb-2">
                                {topicData.title}
                              </h1>
                              <p class="text-parchment-300">
                                Week {topicData.week}
                                <Show when={topicData.order > 1}> • Topic {topicData.order}</Show>
                              </p>
                            </div>
                            <RequireRole minRole="creator">
                              <Button variant="outline" onClick={() => setIsEditing(true)}>
                                Edit
                              </Button>
                            </RequireRole>
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
                      </div>

                      {/* Lecture Section - takes full width on mobile, right column on desktop */}
                      <div class="lg:col-span-1 mt-6 lg:mt-0">
                        <LectureSection
                          lecture={lecture}
                          courseId={courseId()}
                          topicId={topicId()}
                          lectureError={lectureError()}
                          isGeneratingLecture={isGeneratingLecture()}
                          generationTimeout={generationTimeout()}
                          onGenerateLecture={() => {
                            void handleGenerateLecture()
                          }}
                          onLectureDeleted={handleLectureDeleted}
                          onLectureUpdated={handleLectureUpdated}
                          externalJobActive={jobTracker.hasActiveJobs}
                        />
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
