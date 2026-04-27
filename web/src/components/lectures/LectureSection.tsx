import { A } from '@solidjs/router'
import { Download, FileText, Headphones, Pencil, Play, Trash2, Upload } from 'lucide-solid'
import { type Component, createSignal, Show } from 'solid-js'
import { lectureService } from '../../api/services/lecture-service.js'
import type { Lecture } from '../../api/types.js'
import { RequireRole } from '../../auth/RequireRole'
import { useTranslations } from '../../i18n'
import { useAudioPlayer } from '../../utils/audio-player-context.jsx'
import { createJobTracker, getJobMessage } from '../../utils/job-management.js'
import { Alert, Button, ConfirmationModal, MagicButton, MetadataInfo } from '../ui'
import EditSummaryModal from './EditSummaryModal'

interface LectureSectionProps {
  lecture: () => Lecture | null | undefined
  courseId: number
  topicId: number
  lectureError: string
  isGeneratingLecture: boolean
  generationTimeout: boolean
  onGenerateLecture: () => void
  onGenerateLectureText?: () => void
  onLectureDeleted?: () => void
  onLectureUpdated?: () => void
  externalJobActive?: () => boolean
  courseCode?: string
  topicWeek?: number
  topicOrder?: number
}

export const LectureSection: Component<LectureSectionProps> = (props) => {
  const t = useTranslations()
  const audioPlayer = useAudioPlayer()
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [showDeleteModal, setShowDeleteModal] = createSignal(false)
  const [deleteError, setDeleteError] = createSignal('')
  const [isGeneratingAudio, setIsGeneratingAudio] = createSignal(false)
  const [audioError, setAudioError] = createSignal('')
  const [audioTimeout, setAudioTimeout] = createSignal(false)
  const [isUploadingAudio, setIsUploadingAudio] = createSignal(false)
  const [uploadSuccess, setUploadSuccess] = createSignal(false)
  const [isGeneratingSummary, setIsGeneratingSummary] = createSignal(false)
  const [summaryError, setSummaryError] = createSignal('')
  const [showEditSummaryModal, setShowEditSummaryModal] = createSignal(false)
  const [isSavingSummary, setIsSavingSummary] = createSignal(false)
  const [showClearSummaryModal, setShowClearSummaryModal] = createSignal(false)
  const [isClearingSummary, setIsClearingSummary] = createSignal(false)

  const [isGeneratingTimeline, setIsGeneratingTimeline] = createSignal(false)
  const [timelineError, setTimelineError] = createSignal('')
  const [isGeneratingImages, setIsGeneratingImages] = createSignal(false)
  const [imagesError, setImagesError] = createSignal('')

  // Track jobs for this topic AND lecture (lecture ID will be undefined initially,
  // then change when created)
  const jobTracker = createJobTracker({
    topicId: () => props.topicId,
    lectureId: () => props.lecture()?.id, // This will reactively update when lecture is created
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
    onJobComplete: (event) => {
      if (import.meta.env.DEV) {
        console.log('[LectureSection] Job completed:', event.kind, event.id)
      }

      // Clear error messages when jobs complete
      if (event.kind === 'generate_lecture_audio') {
        setAudioError('')
      } else if (event.kind === 'generate_lecture_timeline') {
        setTimelineError('')
      } else if (event.kind === 'remap_lecture_images_timeline') {
        setTimelineError('')
        setImagesError('')
      } else if (
        event.kind === 'generate_lecture_images' ||
        event.kind === 'generate_lecture_slide'
      ) {
        setImagesError('')
      }

      // Always refresh lecture data when any lecture-related job completes
      // Use setTimeout to ensure state updates happen after SSE processing
      setTimeout(() => {
        props.onLectureUpdated?.()
      }, 100)
    },
    onJobFail: (event) => {
      if (import.meta.env.DEV) {
        console.log('[LectureSection] Job failed:', event.kind, event.id)
      }

      if (event.kind === 'generate_lecture_audio') {
        setAudioError(getJobMessage(event.kind, 'failed'))
      } else if (event.kind === 'generate_lecture_summary') {
        setSummaryError(getJobMessage(event.kind, 'failed'))
      } else if (event.kind === 'generate_lecture_timeline') {
        setTimelineError(getJobMessage(event.kind, 'failed'))
      } else if (event.kind === 'remap_lecture_images_timeline') {
        setImagesError(getJobMessage(event.kind, 'failed'))
      } else if (
        event.kind === 'generate_lecture_images' ||
        event.kind === 'generate_lecture_slide'
      ) {
        setImagesError(getJobMessage(event.kind, 'failed'))
      } else if (event.kind === 'generate_lecture_text_only') {
        // Handle text-only generation failures
        // The error will be shown via the lectureError prop from TopicDetail
      }
    },
    onJobStart: (event) => {
      if (import.meta.env.DEV) {
        console.log('[LectureSection] Job started:', event.kind, event.id, event.status)
      }
    },
  })

  // Combined job active check including external jobs - needs to be reactive
  const anyJobActive = () => {
    const trackerActive = jobTracker.hasActiveJobs()
    const externalActive = props.externalJobActive?.() ?? false
    const generatingLecture = props.isGeneratingLecture
    return trackerActive || externalActive || generatingLecture
  }

  const confirmRegeneration = (message: string) => window.confirm(message)

  const uploadAudioDisabled = () =>
    isUploadingAudio() || anyJobActive() || Boolean(props.lecture()?.content)

  const handleDeleteLecture = async () => {
    const lecture = props.lecture()
    if (!lecture) return

    setIsDeleting(true)
    setDeleteError('')

    try {
      await lectureService.deleteLecture(lecture.id)
      setShowDeleteModal(false)
      // Call the callback to refresh the lecture data
      props.onLectureDeleted?.()
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : 'Failed to delete lecture')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleGenerateAudio = async () => {
    const lecture = props.lecture()
    if (!lecture) return

    setIsGeneratingAudio(true)
    setAudioError('')
    setAudioTimeout(false)

    try {
      await lectureService.enqueueGenerateLectureAudio(lecture.id)
    } catch (error) {
      setAudioError(error instanceof Error ? error.message : 'Failed to generate audio')
    } finally {
      setIsGeneratingAudio(false)
    }
  }

  const handleUploadAudio = async (file: File) => {
    const lecture = props.lecture()
    if (!lecture) return

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
      await lectureService.uploadAudio(lecture.id, file)
      setUploadSuccess(true)
      // Refresh lecture data
      props.onLectureUpdated?.()
      // Clear success message after 3 seconds
      setTimeout(() => setUploadSuccess(false), 3000)
    } catch (error) {
      setAudioError(error instanceof Error ? error.message : 'Failed to upload audio')
    } finally {
      setIsUploadingAudio(false)
    }
  }

  const handleGenerateSummary = async () => {
    const lecture = props.lecture()
    if (!lecture) return

    setIsGeneratingSummary(true)
    setSummaryError('')

    try {
      await lectureService.generateSummary(lecture.id)
      // Refresh lecture data to show the new summary
      props.onLectureUpdated?.()
    } catch (error) {
      setSummaryError(error instanceof Error ? error.message : 'Failed to generate summary')
    } finally {
      setIsGeneratingSummary(false)
    }
  }

  const handleEditSummary = async (newSummary: string) => {
    const lecture = props.lecture()
    if (!lecture) return

    setIsSavingSummary(true)
    setSummaryError('')

    try {
      await lectureService.updateLecture(lecture.id, { summary: newSummary })
      setShowEditSummaryModal(false)
      // Refresh lecture data to show the updated summary
      props.onLectureUpdated?.()
    } catch (error) {
      setSummaryError(error instanceof Error ? error.message : 'Failed to update summary')
    } finally {
      setIsSavingSummary(false)
    }
  }

  const handleClearSummary = async () => {
    const lecture = props.lecture()
    if (!lecture) return

    setIsClearingSummary(true)
    setSummaryError('')

    try {
      await lectureService.clearSummary(lecture.id)
      setShowClearSummaryModal(false)
      // Refresh lecture data
      props.onLectureUpdated?.()
    } catch (error) {
      setSummaryError(error instanceof Error ? error.message : 'Failed to clear summary')
    } finally {
      setIsClearingSummary(false)
    }
  }

  const handleGenerateTimeline = async () => {
    const lecture = props.lecture()
    if (!lecture) return

    setIsGeneratingTimeline(true)
    setTimelineError('')

    try {
      await lectureService.enqueueGenerateLectureTimeline(lecture.id)
    } catch (error) {
      setTimelineError(error instanceof Error ? error.message : 'Failed to generate timeline')
    } finally {
      setIsGeneratingTimeline(false)
    }
  }

  const handleGenerateImages = async () => {
    const lecture = props.lecture()
    if (!lecture) return

    setIsGeneratingImages(true)
    setImagesError('')

    try {
      await lectureService.enqueueGenerateLectureImages(lecture.id)
    } catch (error) {
      setImagesError(error instanceof Error ? error.message : 'Failed to generate lecture images')
    } finally {
      setIsGeneratingImages(false)
    }
  }

  return (
    <div class="arcane-card">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-4">
        <h3 class="text-xl font-display text-parchment-100 pr-4">Lecture</h3>
        <Show when={props.lecture()}>
          {(lectureData) => (
            <div class="flex flex-col gap-3 sm:items-end w-full sm:w-auto">
              {/* Essential Actions Group */}
              <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:justify-end sm:items-center w-full">
                <Show when={lectureData().audio_url}>
                  <Button
                    variant="outline"
                    size="sm"
                    class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center gap-2"
                    onClick={() => {
                      const lecture = lectureData()
                      if (lecture.audio_url) {
                        audioPlayer.playTrack({
                          url: lecture.audio_url,
                          title: lecture.title,
                          subtitle: `Revision ${String(lecture.revision)}`,
                          timelineUrl: lecture.timeline_url ?? undefined,
                          imagesTimelineUrl: lecture.images_timeline_url ?? undefined,
                          courseId: props.courseId,
                          lectureId: lecture.id,
                          topicId: props.topicId,
                          courseCode: props.courseCode,
                          topicWeek: props.topicWeek,
                          topicOrder: props.topicOrder,
                        })
                      }
                    }}
                  >
                    <Show
                      when={lectureData().timeline_url}
                      fallback={<Headphones class="h-4 w-4" aria-hidden="true" />}
                    >
                      <Play class="h-4 w-4" aria-hidden="true" />
                    </Show>
                    {lectureData().timeline_url ? t().lectureDetail.play : t().lectureDetail.listen}
                  </Button>
                  <a
                    href={lectureData().audio_download_url || lectureData().audio_url || undefined}
                    download=""
                    class="inline-block w-full sm:w-auto"
                  >
                    <Button
                      variant="outline"
                      size="sm"
                      class="min-h-[44px] sm:min-h-[32px] w-full flex items-center justify-center gap-2"
                    >
                      <Download class="h-4 w-4" aria-hidden="true" />
                      Download
                    </Button>
                  </a>
                </Show>
                <A
                  href={`/courses/${String(props.courseId)}/lectures/${String(lectureData().id)}`}
                  class="inline-block w-full sm:w-auto"
                >
                  <Button
                    variant="primary"
                    size="sm"
                    class="min-h-[44px] sm:min-h-[32px] w-full flex items-center justify-center gap-2"
                  >
                    <FileText class="h-4 w-4" aria-hidden="true" />
                    View
                  </Button>
                </A>
              </div>

              {/* Admin/Creator Actions Group */}
              <RequireRole minRole="creator">
                <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:justify-end sm:items-center w-full pt-3 sm:pt-2 border-t sm:border-t-0 border-parchment-800/30">
                  <MagicButton
                    variant="primary"
                    size="sm"
                    class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center"
                    onClick={() => {
                      if (
                        lectureData().audio_url &&
                        !confirmRegeneration(
                          'Regenerate audio? This replaces the lecture audio and will regenerate the word timeline, then remap the existing lecture image timeline.'
                        )
                      ) {
                        return
                      }
                      void handleGenerateAudio()
                    }}
                    disabled={isGeneratingAudio() || anyJobActive() || isUploadingAudio()}
                  >
                    {isGeneratingAudio()
                      ? 'Generating Audio...'
                      : lectureData().audio_url
                        ? 'Regenerate Audio'
                        : 'Generate Audio'}
                  </MagicButton>
                  <RequireRole minRole="admin">
                    <Show when={lectureData().audio_url}>
                      <MagicButton
                        variant="primary"
                        size="sm"
                        class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center"
                        onClick={() => {
                          if (
                            lectureData().timeline_url &&
                            !confirmRegeneration(
                              'Regenerate timeline? This replaces the word timeline and will remap the existing lecture image timeline without regenerating images.'
                            )
                          ) {
                            return
                          }
                          void handleGenerateTimeline()
                        }}
                        disabled={isGeneratingTimeline() || anyJobActive()}
                      >
                        {isGeneratingTimeline()
                          ? 'Generating Timeline...'
                          : lectureData().timeline_url
                            ? 'Regenerate Timeline'
                            : 'Generate Timeline'}
                      </MagicButton>
                    </Show>
                    <Show when={lectureData().timeline_url}>
                      <MagicButton
                        variant="primary"
                        size="sm"
                        class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center"
                        onClick={() => {
                          if (
                            lectureData().images_timeline_url &&
                            !confirmRegeneration(
                              'Regenerate lecture images? This will delete existing slide images where possible and create a new image timeline with newly generated images.'
                            )
                          ) {
                            return
                          }
                          void handleGenerateImages()
                        }}
                        disabled={isGeneratingImages() || anyJobActive()}
                      >
                        {isGeneratingImages()
                          ? 'Generating Images...'
                          : lectureData().images_timeline_url
                            ? 'Regenerate Lecture Images'
                            : 'Generate Lecture Images'}
                      </MagicButton>
                    </Show>
                    <label
                      for={`audio-file-upload-${String(lectureData().id)}`}
                      class="inline-flex items-center justify-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md border border-mystic-600 bg-mystic-900/20 text-mystic-300 hover:bg-mystic-900/40 hover:border-mystic-500 transition-colors cursor-pointer min-h-[44px] sm:min-h-[32px] w-full sm:w-auto"
                      classList={{
                        'opacity-50 cursor-not-allowed': uploadAudioDisabled(),
                      }}
                      title={
                        lectureData().content
                          ? 'Upload is disabled once lecture text exists.'
                          : undefined
                      }
                    >
                      <Upload class="h-4 w-4" />
                      <span>{isUploadingAudio() ? 'Uploading...' : 'Upload'}</span>
                    </label>
                    <input
                      id={`audio-file-upload-${String(lectureData().id)}`}
                      type="file"
                      accept="audio/mpeg,audio/mp3,.mp3"
                      class="hidden"
                      disabled={uploadAudioDisabled()}
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        if (file) {
                          void handleUploadAudio(file)
                          // Reset the input so the same file can be selected again if needed
                          e.target.value = ''
                        }
                      }}
                    />
                  </RequireRole>
                  <Button
                    variant="danger"
                    size="sm"
                    class="min-h-[44px] sm:min-h-[32px] w-full sm:w-auto flex items-center justify-center gap-2"
                    onClick={() => setShowDeleteModal(true)}
                    disabled={isDeleting()}
                  >
                    <Trash2 class="h-4 w-4" aria-hidden="true" />
                    {isDeleting() ? 'Deleting...' : 'Delete'}
                  </Button>
                </div>
              </RequireRole>
            </div>
          )}
        </Show>
      </div>

      <Show when={props.lectureError}>
        <Alert variant="danger" class="mb-4">
          {props.lectureError}
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
          The audio generation request timed out. It may still complete in the background. Try
          refreshing in a bit.
        </Alert>
      </Show>
      <Show when={uploadSuccess()}>
        <Alert variant="success" class="mb-4">
          Audio file uploaded successfully!
        </Alert>
      </Show>

      {/* Timeline generation error */}
      <Show when={timelineError()}>
        <Alert variant="danger" class="mb-4">
          {timelineError()}
        </Alert>
      </Show>

      {/* Lecture images generation error */}
      <Show when={imagesError()}>
        <Alert variant="danger" class="mb-4">
          {imagesError()}
        </Alert>
      </Show>

      {/* Summary generation error messages */}
      <Show when={summaryError()}>
        <Alert variant="danger" class="mb-4">
          {summaryError()}
        </Alert>
      </Show>

      <Show when={props.lecture()}>
        {(lectureData) => (
          <div class="space-y-4">
            <div>
              <h4 class="text-lg font-medium text-parchment-200">{lectureData().title}</h4>
              <p class="text-sm text-parchment-400">Revision {lectureData().revision}</p>
              <Show when={lectureData().word_count != null}>
                <p class="text-sm text-parchment-400">
                  {lectureData().word_count?.toLocaleString()} words
                </p>
              </Show>
              <Show when={lectureData().summary}>
                <div class="mt-3">
                  <p class="text-parchment-200 font-serif whitespace-pre-wrap">
                    {lectureData().summary}
                  </p>
                  <RequireRole minRole="admin">
                    <div class="mt-3 flex flex-wrap gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowEditSummaryModal(true)}
                        disabled={anyJobActive()}
                      >
                        <Pencil size={14} class="mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => void handleGenerateSummary()}
                        disabled={isGeneratingSummary() || anyJobActive()}
                      >
                        {isGeneratingSummary() ? 'Regenerating...' : 'Regenerate'}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowClearSummaryModal(true)}
                        disabled={anyJobActive()}
                      >
                        <Trash2 size={14} class="mr-1" />
                        Clear
                      </Button>
                    </div>
                  </RequireRole>
                </div>
              </Show>
              <Show when={!lectureData().summary}>
                <RequireRole minRole="creator">
                  <div class="mt-3">
                    <MagicButton
                      variant="primary"
                      size="sm"
                      onClick={() => void handleGenerateSummary()}
                      disabled={isGeneratingSummary() || anyJobActive()}
                    >
                      {isGeneratingSummary() ? 'Generating Summary...' : 'Generate Summary'}
                    </MagicButton>
                  </div>
                </RequireRole>
              </Show>
              <Show when={summaryError()}>
                <Alert variant="danger" class="mt-2">
                  {summaryError()}
                </Alert>
              </Show>
            </div>

            {/* Metadata Section */}
            <div class="pt-3 mt-3 border-t border-parchment-800/30">
              <MetadataInfo
                createdBy={lectureData().student}
                createdWith={lectureData().created_with}
                createdAt={lectureData().created_at}
              />
            </div>
          </div>
        )}
      </Show>

      <Show when={!props.lecture()}>
        <div class="text-center py-8">
          <p class="text-parchment-400 font-serif mb-6">
            No lecture has been created for this topic yet.
          </p>
          <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
            <RequireRole minRole="creator">
              <Show when={props.onGenerateLectureText}>
                <MagicButton
                  variant="primary"
                  class="w-full sm:w-auto"
                  onClick={() => {
                    props.onGenerateLectureText?.()
                  }}
                  disabled={anyJobActive()}
                >
                  {props.isGeneratingLecture
                    ? t().topicDetail.generating
                    : t().topicDetail.generateLectureText}
                </MagicButton>
              </Show>
              <MagicButton
                variant="primary"
                class="w-full sm:w-auto"
                onClick={props.onGenerateLecture}
                disabled={anyJobActive()}
              >
                {props.isGeneratingLecture
                  ? t().topicDetail.generating
                  : t().topicDetail.generateLectureWithAudio}
              </MagicButton>
            </RequireRole>
          </div>
        </div>
      </Show>

      {/* Timeout message */}
      <Show when={props.generationTimeout}>
        <Alert variant="warning" class="mt-4">
          <p class="text-sm">
            The generation request took longer than expected and timed out. This can happen with
            complex content generation. Please try again.
          </p>
        </Alert>
      </Show>

      {/* Delete Confirmation Modal */}
      <Show when={props.lecture()}>
        {(lectureData) => (
          <ConfirmationModal
            isOpen={showDeleteModal()}
            title="Delete Lecture"
            message={
              <div>
                <p>Are you sure you want to delete the lecture "{lectureData().title}"?</p>
                <p class="mt-2 text-sm text-muted">This action cannot be undone.</p>
              </div>
            }
            confirmText="Delete"
            onConfirm={() => void handleDeleteLecture()}
            onCancel={() => setShowDeleteModal(false)}
            isConfirming={isDeleting()}
          />
        )}
      </Show>

      {/* Edit Summary Modal */}
      <Show when={props.lecture()}>
        {(lectureData) => (
          <EditSummaryModal
            isOpen={showEditSummaryModal()}
            initialSummary={lectureData().summary || ''}
            onSave={handleEditSummary}
            onCancel={() => setShowEditSummaryModal(false)}
            isSaving={isSavingSummary()}
          />
        )}
      </Show>

      {/* Clear Summary Confirmation Modal */}
      <Show when={props.lecture()}>
        {(lectureData) => (
          <ConfirmationModal
            isOpen={showClearSummaryModal()}
            title="Clear Summary"
            message={
              <div>
                <p>Are you sure you want to clear the summary for "{lectureData().title}"?</p>
                <p class="mt-2 text-sm text-muted">
                  The summary will be removed, but you can regenerate it later.
                </p>
              </div>
            }
            confirmText="Clear"
            onConfirm={() => void handleClearSummary()}
            onCancel={() => setShowClearSummaryModal(false)}
            isConfirming={isClearingSummary()}
          />
        )}
      </Show>
    </div>
  )
}
