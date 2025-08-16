import { A } from '@solidjs/router'
import { type Component, createSignal, onCleanup, onMount, Show } from 'solid-js'
import { subscribeJobEvents } from '../../api/services/jobs-service.js'
import { lectureService } from '../../api/services/lecture-service.js'
import type { Lecture } from '../../api/types.js'
import { RequireAuth } from '../../auth/RequireAuth'
import { Alert, Button, ConfirmationModal, LoadingSpinner, MagicButton } from '../ui'

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
}

export const LectureSection: Component<LectureSectionProps> = (props) => {
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [showDeleteModal, setShowDeleteModal] = createSignal(false)
  const [deleteError, setDeleteError] = createSignal('')
  const [isGeneratingAudio, setIsGeneratingAudio] = createSignal(false)
  const [audioError, setAudioError] = createSignal('')
  const [audioInfo, setAudioInfo] = createSignal('')
  const [audioTimeout, setAudioTimeout] = createSignal(false)
  const [anyJobActive, setAnyJobActive] = createSignal(false)

  // SSE: subscribe to any job events for this lecture/topic
  onMount(() => {
    const lec = props.lecture()
    const stop = subscribeJobEvents(
      lec ? { lecture_id: lec.id } : { topic_id: props.topicId },
      (ev) => {
        const st = ev.status
        if (st === 'queued' || st === 'running') {
          setAnyJobActive(true)
        }
        if (st === 'done' || st === 'failed' || st === 'cancelled') {
          setAnyJobActive(false)
        }
      }
    )
    onCleanup(() => {
      stop()
    })
  })

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
    setAudioInfo('')
    setAudioTimeout(false)

    try {
      const job = await lectureService.enqueueGenerateLectureAudio(lecture.id)
      setAudioInfo(
        `Audio generation enqueued as Job #${String(job.id)}. Check the Jobs bar for progress.`
      )
    } catch (error) {
      setAudioError(error instanceof Error ? error.message : 'Failed to generate audio')
    } finally {
      setIsGeneratingAudio(false)
    }
  }

  return (
    <div class="arcane-card">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-display text-parchment-100 pr-4">Lecture</h3>
        <Show when={props.lecture()}>
          {(lectureData) => (
            <div class="flex flex-wrap gap-2 items-center">
              {/* Audio actions: listen if available */}
              <Show when={lectureData().audio_url}>
                <a
                  href={lectureData().audio_url || undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-block"
                >
                  <Button variant="outline" size="sm" class="h-8">
                    Listen
                  </Button>
                </a>
              </Show>
              <RequireAuth>
                <MagicButton
                  variant="primary"
                  size="sm"
                  class="h-8"
                  onClick={() => void handleGenerateAudio()}
                  disabled={isGeneratingAudio() || anyJobActive()}
                >
                  {isGeneratingAudio()
                    ? 'Generating Audio...'
                    : lectureData().audio_url
                      ? 'Regenerate Audio'
                      : 'Generate Audio'}
                </MagicButton>
              </RequireAuth>
              <A
                href={`/courses/${String(props.courseId)}/lectures/${String(lectureData().id)}`}
                class="inline-block"
              >
                <Button variant="primary" size="sm" class="h-8">
                  View
                </Button>
              </A>
              <RequireAuth>
                <Button
                  variant="danger"
                  size="sm"
                  class="h-8"
                  onClick={() => setShowDeleteModal(true)}
                  disabled={isDeleting()}
                >
                  {isDeleting() ? 'Deleting...' : 'Delete'}
                </Button>
              </RequireAuth>
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

      <Show when={audioInfo()}>
        <Alert variant="info" class="mb-4">
          {audioInfo()}
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
              <Show when={lectureData().summary}>
                <p class="mt-3 text-parchment-200 font-serif whitespace-pre-wrap">
                  {lectureData().summary}
                </p>
              </Show>
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
            <RequireAuth>
              <A
                href={`/courses/${String(props.courseId)}/topics/${String(props.topicId)}/lectures/new`}
                class="inline-block"
              >
                <Button variant="outline">New Lecture</Button>
              </A>
              <MagicButton
                variant="primary"
                onClick={props.onGenerateLecture}
                disabled={props.isGeneratingLecture || anyJobActive()}
              >
                {props.isGeneratingLecture ? 'Generating...' : 'Generate Lecture'}
              </MagicButton>
            </RequireAuth>
          </div>
        </div>
      </Show>

      {/* Loading indicator for generation */}
      <Show when={props.isGeneratingLecture}>
        <div class="mt-6 p-4 bg-mystic-900/30 border border-mystic-700 rounded-lg">
          <div class="flex items-center justify-center space-x-3">
            <LoadingSpinner />
            <span class="text-sm text-parchment-300">Generating lecture...</span>
          </div>
          <p class="text-xs text-parchment-400 mt-3 text-center">This may take several minutes.</p>
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
