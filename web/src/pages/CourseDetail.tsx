import { A, useNavigate, useParams } from '@solidjs/router'
import { Download, FileText, Headphones } from 'lucide-solid'
import { type Component, createResource, createSignal, For, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { topicService } from '../api/services/topic-service.js'
import type {
  CourseLecturesResponse,
  CourseUpdate,
  DepartmentBrief,
  LectureBrief,
  ProfessorBrief,
  TopicList,
} from '../api/types.js'
import { useAuth } from '../auth/AuthProvider'
import { RequireRole } from '../auth/RequireRole'
import CourseForm from '../components/courses/CourseForm.jsx'
import type { CourseFormData } from '../components/courses/types.jsx'
import { Alert, Button, MagicButton, MetadataInfo } from '../components/ui'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'

// Department Info Component
const DepartmentInfo: Component<{
  departmentData: () => DepartmentBrief | undefined
  loading: boolean
}> = (props) => {
  return (
    <div class="arcane-card">
      <h2 class="text-xl font-display text-parchment-100 mb-4 border-b border-parchment-800/30 pb-2">
        Department
      </h2>
      <Show
        when={!props.loading}
        fallback={<div class="text-parchment-400 font-serif">Loading department...</div>}
      >
        <Show
          when={props.departmentData()}
          fallback={<div class="text-parchment-400 font-serif">Department info not available.</div>}
        >
          {(dept) => {
            const department = dept()
            return (
              <div class="font-serif">
                <A
                  href={`/departments/${String(department.id)}`}
                  class="text-mystic-400 hover:text-mystic-300 transition-colors font-medium"
                >
                  {department.name} ({department.code})
                </A>
                <p class="text-parchment-300 mt-1">Faculty: {department.faculty_name || 'N/A'}</p>
              </div>
            )
          }}
        </Show>
      </Show>
    </div>
  )
}

// Professor Info Component
const ProfessorInfo: Component<{
  professorData: () => ProfessorBrief | undefined
  loading: boolean
}> = (props) => {
  return (
    <div class="arcane-card">
      <h2 class="text-xl font-display text-parchment-100 mb-4 border-b border-parchment-800/30 pb-2">
        Professor
      </h2>
      <Show
        when={!props.loading}
        fallback={<div class="text-parchment-400 font-serif">Loading professor...</div>}
      >
        <Show
          when={props.professorData()}
          fallback={<div class="text-parchment-400 font-serif">Professor info not available.</div>}
        >
          {(prof) => {
            const professor = prof()
            return (
              <div class="font-serif">
                <A
                  href={`/professors/${String(professor.id)}`}
                  class="text-mystic-400 hover:text-mystic-300 transition-colors font-medium"
                >
                  {professor.name}, {professor.title}
                </A>
                <p class="text-parchment-300 pt-3">{professor.specialization}</p>
              </div>
            )
          }}
        </Show>
      </Show>
    </div>
  )
}

// Topics List Component
const TopicsList: Component<{
  topicsData: () => TopicList | undefined
  lecturesData: () => CourseLecturesResponse | undefined
  courseId: number
  courseCode?: string
  loading: boolean
}> = (props) => {
  const audioPlayer = useAudioPlayer()
  return (
    <Show
      when={!props.loading}
      fallback={
        <div class="arcane-card p-6 text-center text-parchment-400 font-serif">
          Loading topics...
        </div>
      }
    >
      <Show
        when={props.topicsData() && (props.topicsData() as TopicList).items.length > 0}
        fallback={
          <div class="arcane-card p-6 text-center text-parchment-400 font-serif">
            No topics defined for this course.
          </div>
        }
      >
        {(() => {
          const topics = (props.topicsData() as TopicList).items
          const lecturesData =
            typeof props.lecturesData === 'function' ? props.lecturesData() : undefined
          const lectures: LectureBrief[] = lecturesData?.lectures || []

          // Sort topics by week, then by order within each week
          const sortedTopics = topics.sort((a, b) => {
            if (a.week !== b.week) {
              return a.week - b.week
            }
            return a.order - b.order
          })

          // Helper function to find lecture for a topic
          const findLectureForTopic = (topicId: number) => {
            return lectures.find((lecture) => lecture.topic_id === topicId)
          }

          return (
            <ul class="space-y-4">
              <For each={sortedTopics}>
                {(topic) => {
                  const lecture = findLectureForTopic(topic.id)
                  return (
                    <li class="arcane-card p-4 hover:bg-parchment-800/20 transition-colors duration-200">
                      <div class="flex items-start justify-between gap-4">
                        <A
                          href={`/courses/${String(props.courseId)}/topics/${String(topic.id)}`}
                          class="flex-1 block"
                        >
                          <p class="text-parchment-300 text-sm mt-1">
                            Week {topic.week}
                            <Show when={topic.order > 1}> • Topic {topic.order}</Show>
                          </p>
                          <p class="text-parchment-100 font-serif">{topic.title}</p>
                          <Show when={lecture}>
                            <p class="text-parchment-400 text-sm mt-2">Lecture</p>
                            <p class="text-parchment-400 text-sm mt-1">{lecture?.title}</p>
                          </Show>
                        </A>
                        <Show when={lecture && (lecture.audio_url || lecture.transcript_url)}>
                          <div class="flex items-center gap-2 shrink-0">
                            <Show when={lecture?.audio_url}>
                              <button
                                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-parchment-800/40 text-mystic-300 hover:text-mystic-200 hover:border-mystic-400 hover:bg-mystic-500/10 transition-colors"
                                aria-label="Play lecture audio"
                                title="Play lecture audio"
                                onClick={(event) => {
                                  event.stopPropagation()
                                  if (lecture?.audio_url) {
                                    audioPlayer.playTrack({
                                      url: lecture.audio_url,
                                      title: lecture.title,
                                      subtitle: `Week ${String(topic.week)} - ${topic.title}`,
                                      courseId: props.courseId,
                                      lectureId: lecture.id,
                                      topicId: topic.id,
                                      courseCode: props.courseCode,
                                      topicWeek: topic.week,
                                      topicOrder: topic.order,
                                    })
                                  }
                                }}
                              >
                                <Headphones class="h-4 w-4" />
                              </button>
                              <a
                                href={
                                  lecture?.audio_download_url ?? lecture?.audio_url ?? undefined
                                }
                                download=""
                                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-parchment-800/40 text-mystic-300 hover:text-mystic-200 hover:border-mystic-400 hover:bg-mystic-500/10 transition-colors"
                                aria-label="Download lecture audio"
                                title="Download lecture audio"
                                onClick={(event) => {
                                  event.stopPropagation()
                                }}
                              >
                                <Download class="h-4 w-4" />
                              </a>
                            </Show>
                            <Show when={lecture}>
                              {(lectureData) => (
                                <A
                                  href={`/courses/${String(props.courseId)}/lectures/${String(lectureData().id)}`}
                                  class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-parchment-800/40 text-mystic-300 hover:text-mystic-200 hover:border-mystic-400 hover:bg-mystic-500/10 transition-colors"
                                  aria-label="Open lecture detail"
                                  title="Open lecture detail"
                                  onClick={(event) => {
                                    event.stopPropagation()
                                  }}
                                >
                                  <FileText class="h-4 w-4" />
                                </A>
                              )}
                            </Show>
                          </div>
                        </Show>
                      </div>
                    </li>
                  )
                }}
              </For>
            </ul>
          )
        })()}
      </Show>
    </Show>
  )
}

const CourseDetail: Component = () => {
  const params = useParams()
  const navigate = useNavigate()
  const auth = useAuth()
  // Ensure params.id exists and is a valid number string before parsing
  const courseId = params.id ? Number.parseInt(params.id, 10) : Number.NaN

  // State for edit mode and form submission
  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')
  const [showDeleteConfirm, setShowDeleteConfirm] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [isExporting, setIsExporting] = createSignal(false)
  const [exportJobId, setExportJobId] = createSignal<number | null>(null)
  const [exportMessage, setExportMessage] = createSignal('')
  const [isPublishing, setIsPublishing] = createSignal(false)

  // Check if courseId is a valid number before creating resources
  const isValidId = !Number.isNaN(courseId)

  const [courseData, { refetch }] = createResource(
    () => (isValidId ? courseId : null), // Pass null if ID is invalid
    courseService.getCourse
  )
  const [professorData] = createResource(
    () => (isValidId ? courseId : null),
    courseService.getCourseProfessor
  )
  const [departmentData] = createResource(
    () => (isValidId ? courseId : null),
    courseService.getCourseDepartment
  )
  const [lecturesData] = createResource(
    () => (isValidId ? courseId : null),
    courseService.getCourseLectures
  )
  const [topicsData] = createResource(
    () => (isValidId ? courseId : null),
    (id) => topicService.listTopicsByCourse(id, 1, 100)
  )

  // Handler for course update form submission
  const handleUpdateCourse = async (formData: CourseFormData) => {
    if (!isValidId) return

    setIsSubmitting(true)
    setError('')

    // Prepare payload for CourseUpdate, converting nulls to undefined for optional fields
    const updatePayload: CourseUpdate = {
      code: formData.code,
      title: formData.title,
      department_id: formData.department_id ?? undefined,
      level: formData.level ?? undefined,
      professor_id: formData.professor_id ?? undefined,
      description: formData.description,
      lectures_per_week: formData.lectures_per_week ?? undefined,
      total_weeks: formData.total_weeks ?? undefined,
      // topics are not part of CourseUpdate in types.ts, handle separately if needed
    }

    try {
      await courseService.updateCourse(courseId, updatePayload)
      setIsEditing(false)
      void refetch()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update course')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handler for canceling edit mode
  const handleCancelEdit = () => {
    setIsEditing(false)
    setError('')
  }

  // Handler for deleting a course
  const handleDeleteCourse = () => {
    if (!isValidId) return

    setIsDeleting(true)

    void courseService
      .deleteCourse(courseId)
      .then(() => {
        // Redirect to courses list after successful deletion
        navigate('/courses')
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to delete course')
        setShowDeleteConfirm(false)
      })
      .finally(() => {
        setIsDeleting(false)
      })
  }

  // Handler for exporting a course
  const handleExportCourse = () => {
    if (!isValidId) return

    setIsExporting(true)
    setError('')
    setExportMessage('')

    void courseService
      .exportCourse(courseId)
      .then((response) => {
        setExportJobId(response.id)
        setExportMessage(
          response.message ||
            `Export job ${String(response.id)} enqueued. Check the Jobs page for status.`
        )
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to export course')
      })
      .finally(() => {
        setIsExporting(false)
      })
  }

  // Handler for publishing a course
  const handlePublishCourse = () => {
    if (!isValidId) return

    setIsPublishing(true)
    setError('')

    void courseService
      .publishCourse(courseId)
      .then(() => {
        void refetch()
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to publish course')
      })
      .finally(() => {
        setIsPublishing(false)
      })
  }

  return (
    <div class="container mx-auto p-6">
      <Show when={isValidId} fallback={<div class="text-parchment-100">Invalid Course ID.</div>}>
        <Show
          when={!courseData.loading}
          fallback={<div class="text-parchment-200 font-serif p-4">Loading course details...</div>}
        >
          <Show
            when={courseData()}
            fallback={<div class="arcane-card p-6 text-center">Course not found.</div>}
          >
            {(course) => (
              <div>
                <div class="flex items-center justify-between gap-2 mb-4">
                  <A
                    href="/courses"
                    class="text-mystic-400 hover:text-mystic-300 transition-colors"
                  >
                    ← Back to Courses
                  </A>
                  <Show when={!isEditing()}>
                    <div class="flex gap-2">
                      <Show when={auth.canModify(course().created_by) && course().status === 'hidden'}>
                        <MagicButton
                          variant="secondary"
                          onClick={handlePublishCourse}
                          disabled={isPublishing()}
                          isLoading={isPublishing()}
                          loadingText="Publishing..."
                        >
                          Publish Course
                        </MagicButton>
                      </Show>
                      <Show when={auth.canModify(course().created_by)}>
                        <Button variant="primary" onClick={() => setIsEditing(true)}>
                          Edit Course
                        </Button>
                        <Button variant="secondary" onClick={() => setShowDeleteConfirm(true)}>
                          Delete
                        </Button>
                      </Show>
                      <RequireRole minRole="admin">
                        <Button
                          variant="outline"
                          onClick={handleExportCourse}
                          disabled={isExporting()}
                        >
                          {isExporting() ? 'Exporting...' : 'Export'}
                        </Button>
                      </RequireRole>
                    </div>
                  </Show>
                </div>

                {/* Error Display */}
                <Show when={error()}>
                  <Alert variant="danger" class="mb-4">
                    {error()}
                  </Alert>
                </Show>

                {/* Export Success Message */}
                <Show when={exportMessage()}>
                  <Alert variant="success" class="mb-4">
                    <div class="flex flex-col gap-2">
                      <p>{exportMessage()}</p>
                      <Show when={exportJobId()}>
                        <A href={`/jobs`} class="text-mystic-400 hover:text-mystic-300 underline">
                          View job status →
                        </A>
                      </Show>
                    </div>
                  </Alert>
                </Show>

                {/* Delete Confirmation Dialog */}
                <Show when={showDeleteConfirm()}>
                  <RequireRole minRole="creator">
                    <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                      <div class="arcane-card p-6 max-w-md w-full">
                        <h2 class="text-xl font-semibold mb-4 text-parchment-100">
                          Confirm Deletion
                        </h2>
                        <p class="text-parchment-200 mb-6">
                          Are you sure you want to delete this course? This action cannot be undone.
                        </p>
                        <div class="flex justify-end gap-3">
                          <Button
                            variant="outline"
                            onClick={() => setShowDeleteConfirm(false)}
                            disabled={isDeleting()}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="secondary"
                            onClick={handleDeleteCourse}
                            disabled={isDeleting()}
                          >
                            {isDeleting() ? 'Deleting...' : 'Delete Course'}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </RequireRole>
                </Show>

                <Show
                  when={!isEditing()}
                  fallback={
                    <RequireRole minRole="creator">
                      <div class="arcane-card p-6 mb-8">
                        <h2 class="text-xl font-semibold mb-4 text-parchment-100">Edit Course</h2>
                        <CourseForm
                          course={course()}
                          onSubmit={handleUpdateCourse}
                          onCancel={handleCancelEdit}
                          isSubmitting={isSubmitting()}
                          error={error()}
                        />
                      </div>
                    </RequireRole>
                  }
                >
                  <div class="flex items-center gap-4 mb-3">
                    <h1 class="text-3xl font-display text-parchment-100">
                      {course().code}: {course().title}
                    </h1>
                    <span
                      class={`px-3 py-1 text-sm font-medium rounded-full ${
                        course().status === 'published'
                          ? 'bg-green-500/20 text-green-300 border border-green-400/30'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-400/30'
                      }`}
                    >
                      {course().status === 'published' ? '✓ Published' : '● Hidden'}
                    </span>
                  </div>
                  <p class="text-base italic text-parchment-200 mb-6 font-serif">
                    {course().description}
                  </p>

                  {/* Metadata Section */}
                  <MetadataInfo
                    createdBy={course().student}
                    createdWith={course().created_with}
                    createdAt={course().created_at}
                    class="mb-6 pb-6 border-b border-parchment-800/30"
                  />

                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    {/* Course Details Section */}
                    <div class="arcane-card">
                      <h2 class="text-xl font-display text-parchment-100 mb-4 border-b border-parchment-800/30 pb-2">
                        Course Details
                      </h2>
                      <div class="space-y-3 font-serif">
                        <p>
                          <span class="text-parchment-300">Level:</span>{' '}
                          <span class="text-parchment-100">{course().level}</span>
                        </p>
                        <p>
                          <span class="text-parchment-300">Lectures per week:</span>{' '}
                          <span class="text-parchment-100">{course().lectures_per_week}</span>
                        </p>
                        <p>
                          <span class="text-parchment-300">Total weeks:</span>{' '}
                          <span class="text-parchment-100">{course().total_weeks}</span>
                        </p>
                      </div>
                    </div>

                    {/* Department and Professor Section */}
                    <div class="space-y-6">
                      <DepartmentInfo
                        departmentData={departmentData}
                        loading={departmentData.loading}
                      />
                      <ProfessorInfo
                        professorData={professorData}
                        loading={professorData.loading}
                      />
                    </div>
                  </div>

                  {/* Topics Section */}
                  <div class="mt-8">
                    <div class="flex items-center justify-between mb-5">
                      <h2 class="text-2xl font-display text-parchment-100">Course Topics</h2>
                      <Button variant="primary">
                        <A href={`/courses/${String(courseId)}/topics`}>Edit Topics</A>
                      </Button>
                    </div>
                    <TopicsList
                      topicsData={topicsData}
                      lecturesData={lecturesData}
                      courseId={courseId}
                      courseCode={course().code}
                      loading={topicsData.loading}
                    />
                  </div>
                </Show>
              </div>
            )}
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default CourseDetail
