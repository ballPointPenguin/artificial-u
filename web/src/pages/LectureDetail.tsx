import { A, useNavigate, useParams } from '@solidjs/router'
import { Download, FileText, Headphones, Play, Upload } from 'lucide-solid'
import { type Component, createMemo, createResource, createSignal, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { lectureService } from '../api/services/lecture-service.js'
import { topicService } from '../api/services/topic-service.js'
import type { Lecture, LectureUpdate } from '../api/types.js'
import { useAuth } from '../auth/AuthProvider'
import { RequireRole } from '../auth/RequireRole'
import { LectureForm } from '../components/lectures/LectureForm.jsx'
import {
  Alert,
  Button,
  ConfirmationModal,
  MagicButton,
  MetadataInfo,
  ShareButton,
} from '../components/ui'
import { useTranslations } from '../i18n/index.js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'
import { createJobTracker } from '../utils/job-management.js'

// Lecture Detail View Component
const LectureDetailView: Component<{
  lecture: Lecture
  onEdit: () => void
  onDelete: () => void
  isDeleting: boolean
  onGenerateAudio: () => Promise<void>
  isGeneratingAudio: boolean
  onUploadAudio: (file: File) => Promise<void>
  isUploadingAudio: boolean
  isJobActive: boolean
  courseId: number
  topicTitle?: string
  courseCode?: string
  topicWeek?: number
  topicOrder?: number
}> = (props) => {
  const auth = useAuth()
  const audioPlayer = useAudioPlayer()
  const t = useTranslations()

  const [isGeneratingTimeline, setIsGeneratingTimeline] = createSignal(false)
  const [timelineError, setTimelineError] = createSignal('')
  const [isGeneratingImages, setIsGeneratingImages] = createSignal(false)
  const [imagesError, setImagesError] = createSignal('')
  const confirmRegeneration = (message: string) => window.confirm(message)
  const uploadAudioDisabled = () =>
    props.isUploadingAudio ||
    props.isGeneratingAudio ||
    props.isJobActive ||
    Boolean(props.lecture.content)

  const handleGenerateTimeline = async () => {
    setIsGeneratingTimeline(true)
    setTimelineError('')
    try {
      await lectureService.enqueueGenerateLectureTimeline(props.lecture.id)
    } catch (error) {
      setTimelineError(error instanceof Error ? error.message : 'Failed to generate timeline')
    } finally {
      setIsGeneratingTimeline(false)
    }
  }

  const handleGenerateImages = async () => {
    setIsGeneratingImages(true)
    setImagesError('')
    try {
      await lectureService.enqueueGenerateLectureImages(props.lecture.id)
    } catch (error) {
      setImagesError(error instanceof Error ? error.message : 'Failed to generate lecture images')
    } finally {
      setIsGeneratingImages(false)
    }
  }

  const handleListen = () => {
    if (!props.lecture.audio_url) return
    audioPlayer.playTrack({
      url: props.lecture.audio_url,
      title: props.lecture.title,
      subtitle: props.topicTitle,
      timelineUrl: props.lecture.timeline_url ?? undefined,
      imagesTimelineUrl: props.lecture.images_timeline_url ?? undefined,
      courseId: props.courseId,
      lectureId: props.lecture.id,
      topicId: props.lecture.topic_id,
      courseCode: props.courseCode,
      topicWeek: props.topicWeek,
      topicOrder: props.topicOrder,
    })
  }

  return (
    <div class="arcane-card">
      <div class="mb-6 flex flex-col gap-4">
        <div class="min-w-0 w-full space-y-1">
          <h1 class="font-display text-3xl break-words text-parchment-100">
            {props.lecture.title}
          </h1>
          <p class="text-parchment-300">
            {t().lectureDetail.revision} {props.lecture.revision}
          </p>
        </div>

        <div class="flex w-full shrink-0 flex-col sm:flex-row sm:flex-wrap items-center gap-3 sm:gap-2 sm:justify-end">
          {/* Essential Actions Group */}
          <div class="flex flex-col sm:flex-row sm:flex-wrap w-full sm:w-auto gap-2">
            {/* Transcript button at top */}
            <Show when={props.lecture.transcript_url}>
              <a
                href={props.lecture.transcript_url || undefined}
                target="_blank"
                rel="noopener noreferrer"
                class="inline-block w-full sm:w-auto"
              >
                <Button
                  variant="secondary"
                  size="sm"
                  class="min-h-[44px] sm:min-h-[32px] w-full flex items-center justify-center gap-2"
                >
                  <FileText class="h-4 w-4" />
                  <span class="hidden sm:inline">{t().lectureDetail.viewTranscript}</span>
                  <span class="sm:hidden">{t().lectureDetail.transcript}</span>
                </Button>
              </a>
            </Show>

            {/* Audio actions: listen and download if available */}
            <Show when={props.lecture.audio_url}>
              <Button
                variant="outline"
                size="sm"
                class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center gap-2"
                onClick={handleListen}
              >
                <Show when={props.lecture.timeline_url} fallback={<Headphones class="h-4 w-4" />}>
                  <Play class="h-4 w-4" />
                </Show>
                <span>
                  {props.lecture.timeline_url ? t().lectureDetail.play : t().lectureDetail.listen}
                </span>
              </Button>
              <a
                href={props.lecture.audio_download_url || props.lecture.audio_url || undefined}
                download=""
                class="inline-block w-full sm:w-auto"
              >
                <Button
                  variant="outline"
                  size="sm"
                  class="min-h-[44px] sm:min-h-[32px] w-full flex items-center justify-center gap-2"
                >
                  <Download class="h-4 w-4" />
                  <span>{t().lectureDetail.download}</span>
                </Button>
              </a>
            </Show>
          </div>

          {/* Admin/Creator Actions Group */}
          <RequireRole minRole="creator">
            <div class="flex flex-col sm:flex-row sm:flex-wrap sm:justify-end w-full sm:w-auto gap-2 pt-3 sm:pt-0 border-t sm:border-t-0 border-parchment-800/30">
              <MagicButton
                variant="primary"
                size="sm"
                class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center whitespace-nowrap"
                onClick={() => {
                  if (
                    props.lecture.audio_url &&
                    !confirmRegeneration(
                      'Regenerate audio? This replaces the lecture audio and will regenerate the word timeline, then remap the existing lecture image timeline.'
                    )
                  ) {
                    return
                  }
                  void props.onGenerateAudio()
                }}
                disabled={props.isGeneratingAudio || props.isUploadingAudio}
              >
                {props.isGeneratingAudio
                  ? t().lectureDetail.generatingAudio
                  : props.lecture.audio_url
                    ? t().lectureDetail.regenerateAudio
                    : t().lectureDetail.generateAudio}
              </MagicButton>
              <RequireRole minRole="admin">
                <Show when={props.lecture.audio_url}>
                  <MagicButton
                    variant="primary"
                    size="sm"
                    class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center whitespace-nowrap"
                    onClick={() => {
                      if (
                        props.lecture.timeline_url &&
                        !confirmRegeneration(
                          'Regenerate timeline? This replaces the word timeline and will remap the existing lecture image timeline without regenerating images.'
                        )
                      ) {
                        return
                      }
                      void handleGenerateTimeline()
                    }}
                    disabled={isGeneratingTimeline() || props.isJobActive}
                  >
                    {isGeneratingTimeline()
                      ? 'Generating Timeline...'
                      : props.lecture.timeline_url
                        ? 'Regenerate Timeline'
                        : 'Generate Timeline'}
                  </MagicButton>
                </Show>
                <Show when={props.lecture.timeline_url}>
                  <MagicButton
                    variant="primary"
                    size="sm"
                    class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center whitespace-nowrap"
                    onClick={() => {
                      if (
                        props.lecture.images_timeline_url &&
                        !confirmRegeneration(
                          'Regenerate lecture images? This will delete existing slide images where possible and create a new image timeline with newly generated images.'
                        )
                      ) {
                        return
                      }
                      void handleGenerateImages()
                    }}
                    disabled={isGeneratingImages() || props.isJobActive}
                  >
                    {isGeneratingImages()
                      ? 'Generating Images...'
                      : props.lecture.images_timeline_url
                        ? 'Regenerate Lecture Images'
                        : 'Generate Lecture Images'}
                  </MagicButton>
                </Show>
                <label
                  for="audio-file-upload"
                  class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md border border-mystic-600 bg-mystic-900/20 text-mystic-300 hover:bg-mystic-900/40 hover:border-mystic-500 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] sm:min-h-[32px] w-full sm:w-auto"
                  classList={{
                    'opacity-50 cursor-not-allowed': uploadAudioDisabled(),
                  }}
                  title={
                    props.lecture.content
                      ? 'Upload is disabled once lecture text exists.'
                      : undefined
                  }
                >
                  <Upload class="h-4 w-4" />
                  <span>
                    {props.isUploadingAudio
                      ? t().lectureDetail.uploading
                      : t().lectureDetail.uploadAudio}
                  </span>
                </label>
                <input
                  id="audio-file-upload"
                  type="file"
                  accept="audio/mpeg,audio/mp3,.mp3"
                  class="hidden"
                  disabled={uploadAudioDisabled()}
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) {
                      void props.onUploadAudio(file)
                      e.target.value = ''
                    }
                  }}
                />
              </RequireRole>
              <Show when={auth.canModify(props.lecture.created_by)}>
                <Button
                  variant="outline"
                  size="sm"
                  class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center whitespace-nowrap"
                  onClick={props.onEdit}
                >
                  {t().common.edit}
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center gap-2 whitespace-nowrap"
                  onClick={props.onDelete}
                  disabled={props.isDeleting}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="lucide lucide-trash-2"
                  >
                    <path d="M3 6h18" />
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                    <line x1="10" x2="10" y1="11" y2="17" />
                    <line x1="14" x2="14" y1="11" y2="17" />
                  </svg>
                  {props.isDeleting ? t().common.deleting : t().common.delete}
                </Button>
              </Show>
            </div>
          </RequireRole>
        </div>
      </div>

      <Show when={timelineError()}>
        <Alert variant="danger" class="mb-4">
          {timelineError()}
        </Alert>
      </Show>
      <Show when={imagesError()}>
        <Alert variant="danger" class="mb-4">
          {imagesError()}
        </Alert>
      </Show>

      {/* Metadata Section */}
      <MetadataInfo
        createdBy={props.lecture.student}
        createdWith={props.lecture.created_with}
        createdAt={props.lecture.created_at}
        class="mb-6 pb-6 border-b border-parchment-800/30"
      />

      {/* Synchronized live captions now live in the Now Playing sheet
          (opened via the Listen button above or the mini player). */}

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
          <p class="text-parchment-400 font-serif italic">{t().lectureDetail.noContent}</p>
        </div>
      </Show>
    </div>
  )
}
const LectureDetail = () => {
  const params = useParams()
  const navigate = useNavigate()
  const t = useTranslations()

  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [showDeleteModal, setShowDeleteModal] = createSignal(false)
  const [error, setError] = createSignal('')
  const [deleteError, setDeleteError] = createSignal('')
  const [isGeneratingAudio, setIsGeneratingAudio] = createSignal(false)
  const [audioError, setAudioError] = createSignal('')
  const [audioTimeout, setAudioTimeout] = createSignal(false)
  const [isUploadingAudio, setIsUploadingAudio] = createSignal(false)
  const [uploadSuccess, setUploadSuccess] = createSignal(false)

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

  const jobTracker = createJobTracker({
    lectureId: () => (isValidIds() ? lectureId() : undefined),
    kinds: [
      'generate_lecture',
      'generate_lecture_text_only',
      'generate_lecture_audio',
      'generate_lecture_timeline',
      'remap_lecture_images_timeline',
      'generate_lecture_images',
      'generate_lecture_slide',
      'generate_lecture_summary',
    ],
    onJobComplete: () => {
      setTimeout(() => {
        void refetchLecture()
      }, 100)
    },
  })

  const anyJobActive = () => jobTracker.hasActiveJobs()

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
      void refetchLecture()
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

  const handleUploadAudio = async (file: File) => {
    if (!isValidIds()) return

    // Validate file type
    if (!file.type.startsWith('audio/')) {
      setAudioError('Please select an audio file (MP3 recommended)')
      return
    }

    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024 // 50MB
    if (file.size > maxSize) {
      setAudioError('File size must be less than 50MB')
      return
    }

    setIsUploadingAudio(true)
    setAudioError('')
    setUploadSuccess(false)

    try {
      await lectureService.uploadAudio(lectureId(), file)
      await refetchLecture()
      setUploadSuccess(true)
      // Clear success message after 3 seconds
      setTimeout(() => setUploadSuccess(false), 3000)
    } catch (error) {
      setAudioError(error instanceof Error ? error.message : 'Failed to upload audio')
    } finally {
      setIsUploadingAudio(false)
    }
  }

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
                  <div class="mb-6 flex flex-wrap items-center justify-between gap-y-3 gap-x-4 text-sm">
                    <div class="flex flex-wrap items-center gap-4">
                      <A
                        href={`/courses/${String(courseId())}`}
                        class="text-mystic-500 hover:text-mystic-300 whitespace-nowrap"
                      >
                        ← {t().courseDetail.backToCourse}
                      </A>
                      <span class="text-parchment-600 hidden sm:inline">•</span>
                      <A
                        href={`/courses/${String(courseId())}/topics/${String(lectureData.topic_id)}`}
                        class="text-mystic-500 hover:text-mystic-300 whitespace-nowrap"
                      >
                        {t().lectureDetail.backToTopic}
                      </A>
                    </div>

                    <ShareButton
                      url={`${window.location.origin}/share/courses/${String(
                        courseId()
                      )}/lectures/${String(lectureId())}`}
                    />

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
                          <div class="flex items-center gap-3 ml-auto sm:ml-0">
                            <Show when={prev}>
                              {(p) => (
                                <A
                                  href={`/courses/${String(courseId())}/topics/${String(p().id)}`}
                                  class="text-mystic-500 hover:text-mystic-300"
                                >
                                  ← {t().topicDetail.previousTopic}
                                </A>
                              )}
                            </Show>
                            <Show when={next}>
                              {(n) => (
                                <A
                                  href={`/courses/${String(courseId())}/topics/${String(n().id)}`}
                                  class="text-mystic-500 hover:text-mystic-300"
                                >
                                  {t().topicDetail.nextTopic} →
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
                        <h2 class="text-lg text-parchment-300 break-words">
                          {courseData().code}: {courseData().title}
                        </h2>
                      </div>
                    )}
                  </Show>

                  <Show when={topic()}>
                    {(topicData) => (
                      <div class="mb-6">
                        <h3 class="text-md text-parchment-400 break-words">
                          {t()
                            .lectureDetail.topicContext.replace('{week}', String(topicData().week))
                            .replace('{order}', String(topicData().order))
                            .replace('{title}', topicData().title)}
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
                      {t().lectureDetail.audioGenerationTimeout}
                    </Alert>
                  </Show>
                  <Show when={uploadSuccess()}>
                    <Alert variant="success" class="mb-4">
                      {t().lectureDetail.audioUploadSuccess}
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
                      onUploadAudio={handleUploadAudio}
                      isUploadingAudio={isUploadingAudio()}
                      isJobActive={anyJobActive()}
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
                    title={t().lectureDetail.deleteLecture}
                    message={
                      <div>
                        <p>
                          {t().lectureDetail.confirmDeleteMessage.replace(
                            '{title}',
                            lectureData.title
                          )}
                        </p>
                        <p class="mt-2 text-sm text-muted">{t().lectureDetail.confirmDeleteUndo}</p>
                      </div>
                    }
                    confirmText={t().lectureDetail.confirmDelete}
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
