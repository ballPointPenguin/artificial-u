import { A, useNavigate, useParams } from '@solidjs/router'
import { type Component, createResource, createSignal, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { lectureService } from '../api/services/lecture-service.js'
import { topicService } from '../api/services/topic-service.js'
import type { Lecture, LectureUpdate } from '../api/types.js'
import { LectureForm } from '../components/lectures/LectureForm.jsx'
import { Alert, Button, ConfirmationModal, MagicButton } from '../components/ui'

// Lecture Detail View Component
const LectureDetailView: Component<{
  lecture: Lecture
  onEdit: () => void
  onDelete: () => void
  isDeleting: boolean
  onGenerateAudio: () => Promise<void>
  isGeneratingAudio: boolean
}> = (props) => {
  return (
    <div class="arcane-card">
      <div class="flex justify-between items-start mb-6">
        <div>
          <h1 class="text-3xl font-display text-parchment-100 mb-2">{props.lecture.title}</h1>
          <p class="text-parchment-300">Revision {props.lecture.revision}</p>
        </div>
        <div class="flex space-x-2">
          {/* Transcript button at top */}
          <Show when={props.lecture.transcript_url}>
            <a
              href={props.lecture.transcript_url || undefined}
              target="_blank"
              rel="noopener noreferrer"
              class="inline-block"
            >
              <Button variant="secondary" size="sm">
                View Transcript
              </Button>
            </a>
          </Show>

          {/* Audio actions: listen if available, otherwise generate */}
          <Show when={props.lecture.audio_url}>
            <a
              href={props.lecture.audio_url || undefined}
              target="_blank"
              rel="noopener noreferrer"
              class="inline-block"
            >
              <Button variant="outline" size="sm">
                Listen
              </Button>
            </a>
          </Show>
          <Show when={!props.lecture.audio_url}>
            <MagicButton
              variant="primary"
              size="sm"
              onClick={() => {
                void props.onGenerateAudio()
              }}
              disabled={props.isGeneratingAudio}
            >
              {props.isGeneratingAudio ? 'Generating Audio...' : 'Generate Audio'}
            </MagicButton>
          </Show>
          <Button variant="outline" onClick={props.onEdit}>
            Edit
          </Button>
          <Button variant="danger" onClick={props.onDelete} disabled={props.isDeleting}>
            {props.isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </div>

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

  // Parse IDs from URL params
  const courseId = Number.parseInt(params.courseId, 10)
  const lectureId = Number.parseInt(params.lectureId, 10)

  const isValidIds = !Number.isNaN(courseId) && !Number.isNaN(lectureId)

  // Fetch lecture, course, and topic data
  const [lecture, { refetch: refetchLecture }] = createResource(
    () => (isValidIds ? lectureId : null),
    lectureService.getLecture
  )

  const [course] = createResource(() => (isValidIds ? courseId : null), courseService.getCourse)

  const [topic] = createResource(
    () => (isValidIds && lecture() ? lecture()?.topic_id : null),
    topicService.getTopic
  )

  const handleSubmitUpdate = async (formData: LectureUpdate) => {
    if (!isValidIds) return

    setIsSubmitting(true)
    setError('')

    try {
      await lectureService.updateLecture(lectureId, formData)
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
    if (!isValidIds) return

    setIsDeleting(true)
    setDeleteError('')

    try {
      await lectureService.deleteLecture(lectureId)
      // Navigate back to the topic page
      const topicId = lecture()?.topic_id
      if (topicId) {
        navigate(`/courses/${String(courseId)}/topics/${String(topicId)}`)
      } else {
        navigate(`/courses/${String(courseId)}`)
      }
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : 'Failed to delete lecture')
      setShowDeleteModal(false)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleGenerateAudio = async () => {
    if (!isValidIds) return

    setIsGeneratingAudio(true)
    setAudioError('')
    setAudioTimeout(false)

    try {
      await lectureService.generateLectureAudio(lectureId, () => setAudioTimeout(true))
      await refetchLecture()
    } catch (error) {
      setAudioError(error instanceof Error ? error.message : 'Failed to generate audio')
    } finally {
      setIsGeneratingAudio(false)
    }
  }

  return (
    <div class="container mx-auto px-4 py-8">
      <Show when={isValidIds} fallback={<div class="text-parchment-100">Invalid Lecture ID.</div>}>
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
                  <div class="mb-6">
                    <A
                      href={`/courses/${String(courseId)}/topics/${String(lectureData.topic_id)}`}
                      class="text-mystic-500 hover:text-mystic-300"
                    >
                      ← Back to Topic
                    </A>
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
                        <h3 class="text-md text-parchment-400">Topic: {topicData().title}</h3>
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
                      <LectureForm
                        courseId={courseId}
                        existingLecture={lectureData}
                        onSubmit={handleSubmitUpdate}
                        onCancel={handleCancelEdit}
                        isLoading={isSubmitting()}
                        error={error() ? { detail: error() } : null}
                      />
                    }
                  >
                    {/* Lecture Detail View */}
                    <LectureDetailView
                      lecture={lectureData}
                      onEdit={() => setIsEditing(true)}
                      onDelete={() => setShowDeleteModal(true)}
                      isDeleting={isDeleting()}
                      onGenerateAudio={handleGenerateAudio}
                      isGeneratingAudio={isGeneratingAudio()}
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
