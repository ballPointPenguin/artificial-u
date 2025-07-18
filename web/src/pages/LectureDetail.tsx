import { A, useParams } from '@solidjs/router'
import { type Component, createResource, createSignal, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { lectureService } from '../api/services/lecture-service.js'
import { topicService } from '../api/services/topic-service.js'
import type { Lecture, LectureUpdate } from '../api/types.js'
import { LectureForm } from '../components/lectures/LectureForm.jsx'
import { Alert, Button } from '../components/ui'

// Lecture Detail View Component
const LectureDetailView: Component<{
  lecture: Lecture
  onEdit: () => void
}> = (props) => {
  return (
    <div class="arcane-card">
      <div class="flex justify-between items-start mb-6">
        <div>
          <h1 class="text-3xl font-display text-parchment-100 mb-2">{props.lecture.title}</h1>
          <p class="text-parchment-300">Revision {props.lecture.revision}</p>
        </div>
        <Button variant="primary" onClick={props.onEdit}>
          Edit Lecture
        </Button>
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

      {/* Lecture Metadata */}
      <LectureMetadata lecture={props.lecture} />
    </div>
  )
}

// Lecture Metadata Component
const LectureMetadata: Component<{
  lecture: Lecture
}> = (props) => {
  return (
    <Show when={props.lecture.summary || props.lecture.audio_url || props.lecture.transcript_url}>
      <div class="border-t border-parchment-800/30 pt-6 mt-6">
        <h3 class="text-lg font-semibold text-parchment-200 mb-4">Additional Resources</h3>

        <Show when={props.lecture.summary}>
          <div class="mb-4">
            <h4 class="text-md font-medium text-parchment-300 mb-2">Summary</h4>
            <p class="text-parchment-400 font-serif">{props.lecture.summary}</p>
          </div>
        </Show>

        <Show when={props.lecture.audio_url}>
          <div class="mb-4">
            <h4 class="text-md font-medium text-parchment-300 mb-2">Audio</h4>
            <a
              href={props.lecture.audio_url || undefined}
              target="_blank"
              rel="noopener noreferrer"
              class="text-mystic-500 hover:text-mystic-300"
            >
              Listen to Audio
            </a>
          </div>
        </Show>

        <Show when={props.lecture.transcript_url}>
          <div class="mb-4">
            <h4 class="text-md font-medium text-parchment-300 mb-2">Transcript</h4>
            <a
              href={props.lecture.transcript_url || undefined}
              target="_blank"
              rel="noopener noreferrer"
              class="text-mystic-500 hover:text-mystic-300"
            >
              View Transcript
            </a>
          </div>
        </Show>
      </div>
    </Show>
  )
}

const LectureDetail = () => {
  const params = useParams()

  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')

  // Parse IDs from URL params
  const courseId = Number.parseInt(params.courseId, 10)
  const lectureId = Number.parseInt(params.lectureId, 10)

  const isValidIds = !Number.isNaN(courseId) && !Number.isNaN(lectureId)

  // Fetch lecture, course, and topic data
  const [lecture] = createResource(() => (isValidIds ? lectureId : null), lectureService.getLecture)

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
                    <LectureDetailView lecture={lectureData} onEdit={() => setIsEditing(true)} />
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

export default LectureDetail
