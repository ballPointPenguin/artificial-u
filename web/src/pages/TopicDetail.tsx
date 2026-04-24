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
import { Alert, Button, MetadataInfo, ShareButton } from '../components/ui'
import { useTranslations } from '../i18n/index.js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'
import { createJobTracker, getJobMessage } from '../utils/job-management.js'

const TopicDetail = () => {
  const params = useParams()
  const t = useTranslations()
  const player = useAudioPlayer()

  /** When Now Playing is open, use a single-column stack (like tablet) so the main column is not split with the docked player. */
  const nowPlayingOpen = () => player.isExpanded()

  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')
  const [lectureError, setLectureError] = createSignal('')
  const [isGeneratingLecture, setIsGeneratingLecture] = createSignal(false)
  const [generationTimeout, setGenerationTimeout] = createSignal(false)

  // Parse IDs from URL params
  const courseId = createMemo(() => Number.parseInt(params.courseId ?? '', 10))
  const topicId = createMemo(() => Number.parseInt(params.topicId ?? '', 10))

  const isValidIds = createMemo(() => !Number.isNaN(courseId()) && !Number.isNaN(topicId()))

  // Fetch topic and course data
  const [topic, { refetch: refetchTopic }] = createResource(
    () => (isValidIds() ? topicId() : null),
    topicService.getTopic
  )

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

  const lectureId = createMemo(() => lecture()?.id)

  // Track jobs for this topic - pass reactive accessor
  const jobTracker = createJobTracker({
    topicId: () => (isValidIds() ? topicId() : undefined),
    lectureId: () => lectureId(),
    kinds: [
      'generate_lecture',
      'generate_lecture_text_only',
      'generate_lecture_audio',
      'generate_lecture_summary',
    ],
    onJobComplete: (event) => {
      if (import.meta.env.DEV) {
        console.log('[TopicDetail] Job completed:', event.kind, event.id)
      }

      if (event.kind === 'generate_lecture' || event.kind === 'generate_lecture_text_only') {
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

      if (event.kind === 'generate_lecture' || event.kind === 'generate_lecture_text_only') {
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
      void refetchTopic()
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

  const handleGenerateLectureText = async () => {
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

      const job = await lectureService.enqueueGenerateLectureTextOnly({
        partial_attributes: {
          course_id: courseId(),
          topic_id: topicId(),
        },
      })

      if (import.meta.env.DEV) {
        console.log('[TopicDetail] Enqueued lecture text generation job:', job.id)
      }

      // Note: Don't set isGeneratingLecture to false here - wait for job completion
      // The jobTracker will handle clearing it when the job completes
    } catch (error) {
      setLectureError(error instanceof Error ? error.message : 'Failed to generate lecture text')
      setIsGeneratingLecture(false)
    }
  }

  return (
    <div class="container mx-auto px-4 py-8">
      <Show
        when={isValidIds()}
        fallback={<div class="text-parchment-100">{t().topicDetail.invalidTopicId}</div>}
      >
        <Show
          when={!topic.loading}
          fallback={
            <div class="text-center py-8 text-parchment-300">{t().topicDetail.loadingTopic}</div>
          }
        >
          <Show
            when={!topic.error}
            fallback={
              <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded">
                {t().common.error}:{' '}
                {topic.error instanceof Error ? topic.error.message : t().topicDetail.loadingTopic}
              </div>
            }
          >
            <Show when={topic()} keyed>
              {(topicData) => (
                <div>
                  {/* Breadcrumb navigation */}
                  <div class="mb-6">
                    <div class="flex flex-wrap items-center justify-between gap-3">
                      <A
                        href={`/courses/${String(courseId())}`}
                        class="text-mystic-500 hover:text-mystic-300 whitespace-nowrap"
                      >
                        ← {t().courseDetail.backToCourse}
                      </A>
                      <ShareButton
                        url={`${window.location.origin}/share/courses/${String(
                          courseId()
                        )}/topics/${String(topicId())}`}
                      />
                    </div>
                  </div>

                  {/* Course context */}
                  <Show when={course()}>
                    {(courseData) => (
                      <div class="mb-6">
                        <h2 class="text-lg text-parchment-300 break-words">
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
                        ? items.findIndex((topicItem) => topicItem.id === curTopic.id)
                        : -1
                      const prev = currentIndex > 0 ? items[currentIndex - 1] : null
                      const next =
                        currentIndex >= 0 && currentIndex < items.length - 1
                          ? items[currentIndex + 1]
                          : null
                      return (
                        <div class="mb-4 flex flex-wrap items-center justify-between gap-y-2 gap-x-4">
                          <div class="min-w-[120px]">
                            <Show when={prev}>
                              {(p) => {
                                const prevId = p().id
                                return (
                                  <A
                                    href={`/courses/${String(courseId())}/topics/${String(prevId)}`}
                                    class="text-mystic-500 hover:text-mystic-300 whitespace-nowrap"
                                  >
                                    ← {t().topicDetail.previousTopic}
                                  </A>
                                )
                              }}
                            </Show>
                          </div>
                          <div class="min-w-[100px] text-right">
                            <Show when={next}>
                              {(n) => {
                                const nextId = n().id
                                return (
                                  <A
                                    href={`/courses/${String(courseId())}/topics/${String(nextId)}`}
                                    class="text-mystic-500 hover:text-mystic-300 whitespace-nowrap"
                                  >
                                    {t().topicDetail.nextTopic} →
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
                    <div
                      classList={{
                        'lg:grid lg:grid-cols-2 lg:gap-6': !nowPlayingOpen(),
                        'flex flex-col gap-6': nowPlayingOpen(),
                      }}
                    >
                      <div class="lg:col-span-1">
                        {/* Topic Detail View */}
                        <div class="arcane-card">
                          <div class="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
                            <div class="flex-1 min-w-0">
                              <h1 class="text-3xl font-display text-parchment-100 mb-2 break-words">
                                {topicData.title}
                              </h1>
                              <p class="text-parchment-300">
                                {t().courseDetail.week} {topicData.week}
                                <Show when={topicData.order > 1}>
                                  {' '}
                                  • {t().courseDetail.topic} {topicData.order}
                                </Show>
                              </p>
                            </div>
                            <RequireRole minRole="creator">
                              <Button
                                variant="outline"
                                class="shrink-0 self-start sm:self-auto"
                                onClick={() => setIsEditing(true)}
                              >
                                {t().topicDetail.editTopic}
                              </Button>
                            </RequireRole>
                          </div>

                          <MetadataInfo
                            createdBy={topicData.student}
                            createdWith={topicData.created_with}
                            createdAt={topicData.created_at}
                            class="mb-6 border-t border-parchment-800/30 pt-6"
                          />

                          {/* Topic Content */}
                          <Show when={topicData.content}>
                            <div class="border-t border-parchment-800/30 pt-6">
                              <TopicContentRenderer content={topicData.content} />
                            </div>
                          </Show>

                          <Show when={!topicData.content}>
                            <div class="border-t border-parchment-800/30 pt-6">
                              <p class="text-parchment-400 font-serif italic">
                                {t().topicDetail.noContent}
                              </p>
                            </div>
                          </Show>
                        </div>
                      </div>

                      <div class="lg:col-span-1" classList={{ 'mt-6 lg:mt-0': !nowPlayingOpen() }}>
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
                          onGenerateLectureText={() => {
                            void handleGenerateLectureText()
                          }}
                          onLectureDeleted={handleLectureDeleted}
                          onLectureUpdated={handleLectureUpdated}
                          externalJobActive={jobTracker.hasActiveJobs}
                          courseCode={course()?.code}
                          topicWeek={topic()?.week}
                          topicOrder={topic()?.order}
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
