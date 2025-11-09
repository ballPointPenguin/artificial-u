import { A } from '@solidjs/router'
import { Download } from 'lucide-solid'
import { type Component, createSignal, Show } from 'solid-js'
import { lectureService } from '../../api/services/lecture-service.js'
import type { Lecture } from '../../api/types.js'
import { RequireRole } from '../../auth/RequireRole'
import { createJobTracker, getJobMessage } from '../../utils/job-management.js'
import { Alert, Button, ConfirmationModal, MagicButton, MetadataInfo } from '../ui'

interface LectureSectionProps {
  lecture: () => Lecture | null | undefined
  courseId: number
  topicId: number
  lectureError: string
  isGeneratingLecture: boolean
  generationTimeout: boolean
  onGenerateLecture: () => void
  onLectureDeleted?: () => void
  onLectureUpdated?: () => void
  externalJobActive?: () => boolean
}

export const LectureSection: Component<LectureSectionProps> = (props) => {
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [showDeleteModal, setShowDeleteModal] = createSignal(false)
  const [deleteError, setDeleteError] = createSignal('')
  const [isGeneratingAudio, setIsGeneratingAudio] = createSignal(false)
  const [audioError, setAudioError] = createSignal('')
  const [audioTimeout, setAudioTimeout] = createSignal(false)

  // Track jobs for this topic AND lecture (lecture ID will be undefined initially,
  // then change when created)
  const jobTracker = createJobTracker({
    topicId: () => props.topicId,
    lectureId: () => props.lecture()?.id, // This will reactively update when lecture is created
    kinds: ['generate_lecture', 'generate_lecture_audio', 'generate_lecture_summary'],
    onJobComplete: (event) => {
      if (import.meta.env.DEV) {
        console.log('[LectureSection] Job completed:', event.kind, event.id)
      }

      // Clear error messages when jobs complete
      if (event.kind === 'generate_lecture_audio') {
        setAudioError('')
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

  return (
    <div class="arcane-card">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-4">
        <h3 class="text-xl font-display text-parchment-100 pr-4">Lecture</h3>
        <Show when={props.lecture()}>
          {(lectureData) => (
            <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:justify-end sm:items-center">
              {/* Audio actions: listen and download if available */}
              <Show when={lectureData().audio_url}>
                <a
                  href={lectureData().audio_url || undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-block"
                >
                  <Button variant="outline" size="sm" class="h-8 w-full sm:w-auto">
                    Listen
                  </Button>
                </a>
                <a
                  href={lectureData().audio_download_url || lectureData().audio_url || undefined}
                  download=""
                  class="inline-block"
                >
                  <Button
                    variant="outline"
                    size="sm"
                    class="h-8 w-9 p-0"
                    aria-label="Download lecture audio"
                  >
                    <Download class="h-4 w-4" />
                  </Button>
                </a>
              </Show>
              <RequireRole minRole="creator">
                <MagicButton
                  variant="primary"
                  size="sm"
                  class="h-8 w-full sm:w-auto"
                  onClick={() => void handleGenerateAudio()}
                  disabled={isGeneratingAudio() || anyJobActive()}
                >
                  {isGeneratingAudio()
                    ? 'Generating Audio...'
                    : lectureData().audio_url
                      ? 'Regenerate Audio'
                      : 'Generate Audio'}
                </MagicButton>
              </RequireRole>
              <A
                href={`/courses/${String(props.courseId)}/lectures/${String(lectureData().id)}`}
                class="inline-block"
              >
                <Button variant="primary" size="sm" class="h-8 w-full sm:w-auto">
                  View
                </Button>
              </A>
              <RequireRole minRole="creator">
                <Button
                  variant="danger"
                  size="sm"
                  class="h-8 w-full sm:w-auto"
                  onClick={() => setShowDeleteModal(true)}
                  disabled={isDeleting()}
                >
                  {isDeleting() ? 'Deleting...' : 'Delete'}
                </Button>
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
                <p class="mt-3 text-parchment-200 font-serif whitespace-pre-wrap">
                  {lectureData().summary}
                </p>
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
          <div class="flex justify-center space-x-4">
            <RequireRole minRole="creator">
              <Show
                when={!anyJobActive()}
                fallback={
                  <Button variant="outline" disabled={true}>
                    New Lecture
                  </Button>
                }
              >
                <A
                  href={`/courses/${String(props.courseId)}/topics/${String(props.topicId)}/lectures/new`}
                  class="inline-block"
                >
                  <Button variant="outline">New Lecture</Button>
                </A>
              </Show>
              <MagicButton
                variant="primary"
                onClick={props.onGenerateLecture}
                disabled={anyJobActive()}
              >
                {props.isGeneratingLecture ? 'Generating...' : 'Generate Lecture'}
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
    </div>
  )
}
