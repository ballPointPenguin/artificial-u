import { A, useNavigate, useParams } from '@solidjs/router'
import { Download, FileText, Headphones } from 'lucide-solid'
import {
  type Component,
  createMemo,
  createResource,
  createSignal,
  onCleanup,
  onMount,
  Show,
} from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { type JobRow, listJobs } from '../api/services/jobs-service.js'
import { lectureService } from '../api/services/lecture-service.js'
import { topicService } from '../api/services/topic-service.js'
import type { Lecture, LectureUpdate } from '../api/types.js'
import { useAuth } from '../auth/AuthProvider'
import { RequireRole } from '../auth/RequireRole'
import { LectureForm } from '../components/lectures/LectureForm.jsx'
import { Alert, Button, ConfirmationModal, MagicButton, MetadataInfo } from '../components/ui'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'
import { getJobEventHub } from '../utils/job-events-hub.js'

// Lecture Detail View Component
const LectureDetailView: Component<{
  lecture: Lecture
  onEdit: () => void
  onDelete: () => void
  isDeleting: boolean
  onGenerateAudio: () => Promise<void>
  isGeneratingAudio: boolean
  courseId: number
  topicTitle?: string
  courseCode?: string
  topicWeek?: number
  topicOrder?: number
}> = (props) => {
  const auth = useAuth()
  const audioPlayer = useAudioPlayer()

  return (
    <div class="arcane-card">
      <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between mb-6">
        <div class="space-y-1">
          <h1 class="text-3xl font-display text-parchment-100">{props.lecture.title}</h1>
          <p class="text-parchment-300">Revision {props.lecture.revision}</p>
        </div>
        <div class="flex flex-wrap items-center gap-2 md:justify-end">
          {/* Transcript button at top */}
          <Show when={props.lecture.transcript_url}>
            <a
              href={props.lecture.transcript_url || undefined}
              target="_blank"
              rel="noopener noreferrer"
              class="inline-block"
            >
              <Button variant="secondary" size="sm" class="inline-flex items-center gap-2">
                <FileText class="h-4 w-4" />
                <span class="hidden sm:inline">View Transcript</span>
                <span class="sm:hidden">Transcript</span>
              </Button>
            </a>
          </Show>

          {/* Audio actions: listen and download if available, plus generate/regenerate */}
          <Show when={props.lecture.audio_url}>
            <Button
              variant="outline"
              size="sm"
              class="inline-flex items-center gap-2"
              onClick={() => {
                if (props.lecture.audio_url) {
                  audioPlayer.playTrack({
                    url: props.lecture.audio_url,
                    title: props.lecture.title,
                    subtitle: props.topicTitle,
                    courseId: props.courseId,
                    lectureId: props.lecture.id,
                    topicId: props.lecture.topic_id,
                    courseCode: props.courseCode,
                    topicWeek: props.topicWeek,
                    topicOrder: props.topicOrder,
                  })
                }
              }}
            >
              <Headphones class="h-4 w-4" />
              <span>Listen</span>
            </Button>
            <a
              href={props.lecture.audio_download_url || props.lecture.audio_url || undefined}
              download=""
              class="inline-block"
            >
              <Button variant="outline" size="sm" class="inline-flex items-center gap-2">
                <Download class="h-4 w-4" />
                <span>Download</span>
              </Button>
            </a>
          </Show>
          <RequireRole minRole="creator">
            <MagicButton
              variant="primary"
              size="sm"
              class="whitespace-nowrap"
              onClick={() => {
                void props.onGenerateAudio()
              }}
              disabled={props.isGeneratingAudio}
            >
              {props.isGeneratingAudio
                ? 'Generating Audio...'
                : props.lecture.audio_url
                  ? 'Regenerate Audio'
                  : 'Generate Audio'}
            </MagicButton>
          </RequireRole>
          <Show when={auth.canModify(props.lecture.created_by)}>
            <Button variant="outline" size="sm" class="whitespace-nowrap" onClick={props.onEdit}>
              Edit
            </Button>
            <Button
              variant="danger"
              size="sm"
              class="whitespace-nowrap"
              onClick={props.onDelete}
              disabled={props.isDeleting}
            >
              {props.isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </Show>
        </div>
      </div>

      {/* Metadata Section */}
      <MetadataInfo
        createdBy={props.lecture.student}
        createdWith={props.lecture.created_with}
        createdAt={props.lecture.created_at}
        class="mb-6 pb-6 border-b border-parchment-800/30"
      />

      {/* Lecture Content */}
      <Show when={props.lecture.content}>
        <div class="border-t border-parchment-800/30 pt-6">
          <div class="prose prose-invert max-w-none">
            <pre class="whitespace-pre-wrap text-parchment-200 font-serif">
              {props.lecture.content}
            </pre>
          </div>
        </div>
      </Show>

      <Show when={!props.lecture.content}>
        <div class="border-t border-parchment-800/30 pt-6">
          <p class="text-parchment-400 font-serif italic">No content defined for this lecture.</p>
        </div>
      </Show>

      {/* Additional Resources removed per request */}
    </div>
  )
}

const LectureDetail = () => {
  const params = useParams()
  const navigate = useNavigate()

  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [showDeleteModal, setShowDeleteModal] = createSignal(false)
  const [error, setError] = createSignal('')
  const [deleteError, setDeleteError] = createSignal('')
  const [isGeneratingAudio, setIsGeneratingAudio] = createSignal(false)
  const [audioError, setAudioError] = createSignal('')
  const [audioTimeout, setAudioTimeout] = createSignal(false)
  const [anyJobActive, setAnyJobActive] = createSignal(false)

  // Parse IDs from URL params
  const courseId = createMemo(() => Number.parseInt(params.courseId ?? '', 10))
  const lectureId = createMemo(() => Number.parseInt(params.lectureId ?? '', 10))

  const isValidIds = createMemo(() => !Number.isNaN(courseId()) && !Number.isNaN(lectureId()))

  // Fetch lecture, course, and topic data
  const [lecture, { refetch: refetchLecture }] = createResource(
    () => (isValidIds() ? lectureId() : null),
    lectureService.getLecture
  )

  const [course] = createResource(() => (isValidIds() ? courseId() : null), courseService.getCourse)

  const [topic] = createResource(
    () => (isValidIds() && lecture() ? lecture()?.topic_id : null),
    topicService.getTopic
  )

  // For prev/next topic nav: fetch topics for the lecture's course
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

  const handleSubmitUpdate = async (formData: LectureUpdate) => {
    if (!isValidIds()) return

    setIsSubmitting(true)
    setError('')

    try {
      await lectureService.updateLecture(lectureId(), formData)
      setIsEditing(false)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update lecture')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setError('')
  }

  const handleDeleteLecture = async () => {
    if (!isValidIds()) return

    setIsDeleting(true)
    setDeleteError('')

    try {
      await lectureService.deleteLecture(lectureId())
      // Navigate back to the topic page
      const topicIdVal = lecture()?.topic_id
      if (topicIdVal) {
        navigate(`/courses/${String(courseId())}/topics/${String(topicIdVal)}`)
      } else {
        navigate(`/courses/${String(courseId())}`)
      }
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : 'Failed to delete lecture')
      setShowDeleteModal(false)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleGenerateAudio = async () => {
    if (!isValidIds()) return

    setIsGeneratingAudio(true)
    setAudioError('')
    setAudioTimeout(false)

    try {
      await lectureService.generateLectureAudio(lectureId(), () => setAudioTimeout(true))
      await refetchLecture()
    } catch (error) {
      setAudioError(error instanceof Error ? error.message : 'Failed to generate audio')
    } finally {
      setIsGeneratingAudio(false)
    }
  }

  // Subscribe to job events for this lecture to disable actions while active
  onMount(() => {
    // Initial snapshot of any in-flight jobs for this lecture
    void (async () => {
      try {
        const inflight: JobRow[] = await listJobs({
          status: 'running',
          lecture_id: lectureId(),
        })
        const queued: JobRow[] = await listJobs({
          status: 'queued',
          lecture_id: lectureId(),
        })
        setAnyJobActive([...inflight, ...queued].length > 0)
      } catch {
        // ignore
      }
    })()

    const id = lectureId()
    if (!Number.isNaN(id)) {
      const hub = getJobEventHub()
      const unsubscribe = hub.subscribe({ lectureId: id }, (ev) => {
        const st = ev.status
        if (st === 'queued' || st === 'running') {
          setAnyJobActive(true)
        }
        if (st === 'done' || st === 'failed' || st === 'cancelled') {
          setAnyJobActive(false)
        }
      })
      onCleanup(() => {
        unsubscribe()
      })
    }
  })

  return (
    <div class="container mx-auto px-4 py-8">
      <Show
        when={isValidIds()}
        fallback={<div class="text-parchment-100">Invalid Lecture ID.</div>}
      >
        <Show
          when={!lecture.loading}
          fallback={<div class="text-center py-8 text-parchment-300">Loading lecture...</div>}
        >
          <Show
            when={!lecture.error}
            fallback={
              <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded">
                Error:{' '}
                {lecture.error instanceof Error ? lecture.error.message : 'Failed to load lecture'}
              </div>
            }
          >
            <Show when={lecture()} keyed>
              {(lectureData) => (
                <div>
                  {/* Breadcrumb navigation */}
                  <div class="mb-6 flex items-center justify-between text-sm">
                    <div class="flex items-center space-x-4">
                      <A
                        href={`/courses/${String(courseId())}`}
                        class="text-mystic-500 hover:text-mystic-300"
                      >
                        ← Back to Course
                      </A>
                      <span class="text-parchment-600">•</span>
                      <A
                        href={`/courses/${String(courseId())}/topics/${String(lectureData.topic_id)}`}
                        class="text-mystic-500 hover:text-mystic-300"
                      >
                        Back to Topic
                      </A>
                    </div>

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
                          <div class="flex items-center gap-3">
                            <Show when={prev}>
                              {(p) => (
                                <A
                                  href={`/courses/${String(courseId())}/topics/${String(p().id)}`}
                                  class="text-mystic-500 hover:text-mystic-300"
                                >
                                  ← Previous Topic
                                </A>
                              )}
                            </Show>
                            <Show when={next}>
                              {(n) => (
                                <A
                                  href={`/courses/${String(courseId())}/topics/${String(n().id)}`}
                                  class="text-mystic-500 hover:text-mystic-300"
                                >
                                  Next Topic →
                                </A>
                              )}
                            </Show>
                          </div>
                        )
                      })()}
                    </Show>
                  </div>

                  {/* Course and Topic context */}
                  <Show when={course()}>
                    {(courseData) => (
                      <div class="mb-6">
                        <h2 class="text-lg text-parchment-300">
                          {courseData().code}: {courseData().title}
                        </h2>
                      </div>
                    )}
                  </Show>

                  <Show when={topic()}>
                    {(topicData) => (
                      <div class="mb-6">
                        <h3 class="text-md text-parchment-400">
                          Topic: Week {topicData().week} · Lecture {topicData().order} —{' '}
                          {topicData().title}
                        </h3>
                      </div>
                    )}
                  </Show>

                  {/* Error Display */}
                  <Show when={error()}>
                    <Alert variant="danger" class="mb-4">
                      {error()}
                    </Alert>
                  </Show>

                  <Show when={deleteError()}>
                    <Alert variant="danger" class="mb-4">
                      {deleteError()}
                    </Alert>
                  </Show>

                  {/* Audio generation error/timeout messages */}
                  <Show when={audioError()}>
                    <Alert variant="danger" class="mb-4">
                      {audioError()}
                    </Alert>
                  </Show>
                  <Show when={audioTimeout()}>
                    <Alert variant="warning" class="mb-4">
                      The audio generation request timed out. It may still complete in the
                      background. Try refreshing in a bit.
                    </Alert>
                  </Show>

                  <Show
                    when={!isEditing()}
                    fallback={
                      <RequireRole minRole="creator">
                        <LectureForm
                          courseId={courseId()}
                          existingLecture={lectureData}
                          onSubmit={handleSubmitUpdate}
                          onCancel={handleCancelEdit}
                          isLoading={isSubmitting()}
                          error={error() ? { detail: error() } : null}
                        />
                      </RequireRole>
                    }
                  >
                    {/* Lecture Detail View */}
                    <LectureDetailView
                      lecture={lectureData}
                      onEdit={() => {
                        setIsEditing(true)
                      }}
                      onDelete={() => {
                        setShowDeleteModal(true)
                      }}
                      isDeleting={isDeleting()}
                      onGenerateAudio={handleGenerateAudio}
                      isGeneratingAudio={isGeneratingAudio() || anyJobActive()}
                      courseId={courseId()}
                      topicTitle={topic()?.title}
                      courseCode={course()?.code}
                      topicWeek={topic()?.week}
                      topicOrder={topic()?.order}
                    />
                  </Show>

                  {/* Delete Confirmation Modal */}
                  <ConfirmationModal
                    isOpen={showDeleteModal()}
                    title="Delete Lecture"
                    message={
                      <div>
                        <p>Are you sure you want to delete the lecture "{lectureData.title}"?</p>
                        <p class="mt-2 text-sm text-muted">This action cannot be undone.</p>
                      </div>
                    }
                    confirmText="Delete"
                    onConfirm={() => {
                      void handleDeleteLecture()
                    }}
                    onCancel={() => setShowDeleteModal(false)}
                    isConfirming={isDeleting()}
                  />
                </div>
              )}
            </Show>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default LectureDetail
