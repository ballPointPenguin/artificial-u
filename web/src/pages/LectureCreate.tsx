import { A, useNavigate, useParams } from '@solidjs/router'
import { createResource, createSignal, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { lectureService } from '../api/services/lecture-service.js'
import { topicService } from '../api/services/topic-service.js'
import type { LectureCreate, LectureUpdate } from '../api/types.js'
import { LectureForm } from '../components/lectures/LectureForm.jsx'
import { Alert } from '../components/ui'

const LectureCreatePage = () => {
  const params = useParams()
  const navigate = useNavigate()

  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')

  // Parse IDs from URL params
  const courseId = Number.parseInt(params.courseId, 10)
  const topicId = Number.parseInt(params.topicId, 10)

  const isValidIds = !Number.isNaN(courseId) && !Number.isNaN(topicId)

  // Fetch course and topic data for context
  const [course] = createResource(() => (isValidIds ? courseId : null), courseService.getCourse)
  const [topic] = createResource(() => (isValidIds ? topicId : null), topicService.getTopic)

  const handleSubmitCreate = async (formData: LectureCreate | LectureUpdate) => {
    if (!isValidIds) return

    setIsSubmitting(true)
    setError('')

    try {
      // Since we're creating a new lecture, we know it's LectureCreate type
      const newLecture = await lectureService.createLecture(formData as LectureCreate)
      // Navigate to the newly created lecture
      navigate(`/courses/${String(courseId)}/lectures/${String(newLecture.id)}`)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create lecture')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = () => {
    // Navigate back to the topic detail page
    navigate(`/courses/${String(courseId)}/topics/${String(topicId)}`)
  }

  return (
    <div class="container mx-auto px-4 py-8">
      <Show
        when={isValidIds}
        fallback={<div class="text-parchment-100">Invalid Course or Topic ID.</div>}
      >
        <div>
          {/* Breadcrumb navigation */}
          <div class="mb-6">
            <A
              href={`/courses/${String(courseId)}/topics/${String(topicId)}`}
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

          {/* Lecture Creation Form */}
          <LectureForm
            courseId={courseId}
            topicId={topicId}
            onSubmit={handleSubmitCreate}
            onCancel={handleCancel}
            isLoading={isSubmitting()}
            error={error() ? { detail: error() } : null}
          />
        </div>
      </Show>
    </div>
  )
}

export default LectureCreatePage
