import { A, useNavigate, useParams } from '@solidjs/router'
import { Download, FileText, Film, Headphones, LoaderCircle, Play } from 'lucide-solid'
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
import CourseStatusBadge from '../components/courses/CourseStatusBadge.jsx'
import type { CourseFormData } from '../components/courses/types.jsx'
import { Alert, Button, MagicButton, MetadataInfo, ShareButton } from '../components/ui'
import { useTranslations } from '../i18n'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'
import { adoptJobHandoff } from '../utils/job-management.js'

const COURSE_CREATION_HANDOFF_KINDS = [
  'create_course',
  'generate_course_image',
  'generate_topics_for_course',
  'generate_topic_for_course_slot',
]

const TOPIC_GENERATION_JOB_KINDS = new Set([
  'generate_topics_for_course',
  'generate_topic_for_course_slot',
])

function isTopicGenerationJob(kind: string): boolean {
  return TOPIC_GENERATION_JOB_KINDS.has(kind)
}

// Department Info Component
const DepartmentInfo: Component<{
  departmentData: () => DepartmentBrief | undefined
  loading: boolean
}> = (props) => {
  const t = useTranslations()
  return (
    <div class="arcane-card">
      <h2 class="text-xl font-display text-parchment-100 mb-4 border-b border-parchment-800/30 pb-2">
        {t().courseDetail.department}
      </h2>
      <Show
        when={!props.loading}
        fallback={
          <div class="text-parchment-400 font-serif">{t().courseDetail.loadingDepartment}</div>
        }
      >
        <Show
          when={props.departmentData()}
          fallback={
            <div class="text-parchment-400 font-serif">
              {t().courseDetail.departmentNotAvailable}
            </div>
          }
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
                <p class="text-parchment-300 mt-1">
                  {t().courseDetail.faculty}: {department.faculty_name || t().common.nA}
                </p>
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
  const t = useTranslations()
  return (
    <div class="arcane-card">
      <h2 class="text-xl font-display text-parchment-100 mb-4 border-b border-parchment-800/30 pb-2">
        {t().courseDetail.professor}
      </h2>
      <Show
        when={!props.loading}
        fallback={
          <div class="text-parchment-400 font-serif">{t().courseDetail.loadingProfessor}</div>
        }
      >
        <Show
          when={props.professorData()}
          fallback={
            <div class="text-parchment-400 font-serif">
              {t().courseDetail.professorNotAvailable}
            </div>
          }
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
  isGenerating?: boolean
}> = (props) => {
  const t = useTranslations()
  const audioPlayer = useAudioPlayer()
  return (
    <Show
      when={!props.loading}
      fallback={
        <div class="arcane-card p-6 text-center text-parchment-400 font-serif">
          {t().courseDetail.loadingTopics}
        </div>
      }
    >
      <Show
        when={props.topicsData() && (props.topicsData() as TopicList).items.length > 0}
        fallback={
          <div class="arcane-card p-6 text-center text-parchment-400 font-serif">
            <Show when={props.isGenerating} fallback={t().courseDetail.noTopicsDefined}>
              <div class="flex items-center justify-center gap-3">
                <LoaderCircle class="h-5 w-5 animate-spin text-mystic-400" />
                <span>{t().courseDetail.generatingTopics}</span>
              </div>
            </Show>
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
                            {t().courseDetail.week} {topic.week}
                            <Show when={topic.order > 1}>
                              {' '}
                              • {t().courseDetail.topic} {topic.order}
                            </Show>
                          </p>
                          <p class="text-parchment-100 font-serif">{topic.title}</p>
                          <Show when={lecture}>
                            <p class="text-parchment-400 text-sm mt-2">
                              {t().courseDetail.lecture}
                            </p>
                            <p class="text-parchment-400 text-sm mt-1">{lecture?.title}</p>
                          </Show>
                        </A>
                        <Show when={lecture && (lecture.audio_url || lecture.transcript_url)}>
                          <div class="flex items-center gap-2 shrink-0">
                            <Show when={lecture?.audio_url}>
                              <button
                                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-parchment-800/40 text-mystic-300 hover:text-mystic-200 hover:border-mystic-400 hover:bg-mystic-500/10 transition-colors"
                                aria-label={
                                  lecture?.timeline_url
                                    ? t().courseDetail.playAudio
                                    : t().courseDetail.listenAudio
                                }
                                title={
                                  lecture?.timeline_url
                                    ? t().courseDetail.playAudio
                                    : t().courseDetail.listenAudio
                                }
                                onClick={(event) => {
                                  event.stopPropagation()
                                  if (lecture?.audio_url) {
                                    audioPlayer.playTrack({
                                      url: lecture.audio_url,
                                      title: lecture.title,
                                      subtitle: `${t().courseDetail.week} ${String(topic.week)} - ${topic.title}`,
                                      timelineUrl: lecture.timeline_url ?? undefined,
                                      imagesTimelineUrl: lecture.images_timeline_url ?? undefined,
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
                                <Show
                                  when={lecture?.timeline_url}
                                  fallback={<Headphones class="h-4 w-4" />}
                                >
                                  <Show
                                    when={lecture?.images_timeline_url}
                                    fallback={<Play class="h-4 w-4" />}
                                  >
                                    <Film class="h-4 w-4" />
                                  </Show>
                                </Show>
                              </button>
                              <a
                                href={
                                  lecture?.audio_download_url ?? lecture?.audio_url ?? undefined
                                }
                                download=""
                                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-parchment-800/40 text-mystic-300 hover:text-mystic-200 hover:border-mystic-400 hover:bg-mystic-500/10 transition-colors"
                                aria-label={t().courseDetail.downloadAudio}
                                title={t().courseDetail.downloadAudio}
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
                                  aria-label={t().courseDetail.openDetail}
                                  title={t().courseDetail.openDetail}
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
  const t = useTranslations()
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
  const [isGeneratingImage, setIsGeneratingImage] = createSignal(false)
  const [imageGenerationError, setImageGenerationError] = createSignal('')

  // Check if courseId is a valid number before creating resources
  const isValidId = !Number.isNaN(courseId)

  const [courseData, { refetch: refetchCourse }] = createResource(
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
  const [topicsData, { refetch: refetchTopics }] = createResource(
    () => (isValidId ? courseId : null),
    (id) => topicService.listTopicsByCourse(id, 1, 100)
  )

  const [activeImageJobIds, setActiveImageJobIds] = createSignal<Set<number>>(new Set())
  const [activeTopicJobIds, setActiveTopicJobIds] = createSignal<Set<number>>(new Set())

  const markActiveJob = (setter: typeof setActiveImageJobIds, jobId: number) => {
    setter((prev) => {
      if (prev.has(jobId)) return prev
      const next = new Set(prev)
      next.add(jobId)
      return next
    })
  }

  const clearActiveJob = (setter: typeof setActiveImageJobIds, jobId: number) => {
    setter((prev) => {
      if (!prev.has(jobId)) return prev
      const next = new Set(prev)
      next.delete(jobId)
      return next
    })
  }

  const hasActiveImageJobs = () => activeImageJobIds().size > 0
  const hasActiveTopicJobs = () => activeTopicJobIds().size > 0

  adoptJobHandoff({
    entity: () => (isValidId ? { type: 'course', id: courseId } : null),
    kinds: COURSE_CREATION_HANDOFF_KINDS,
    fallback: () => {
      const course = courseData()
      const topics = topicsData()
      if (!isValidId || courseData.loading || topicsData.loading || !course || !topics) {
        return false
      }
      return !course.image_url || topics.items.length === 0
    },
    onJobStart: (event) => {
      if (event.kind === 'generate_course_image') {
        markActiveJob(setActiveImageJobIds, event.id)
      }
      if (isTopicGenerationJob(event.kind)) {
        markActiveJob(setActiveTopicJobIds, event.id)
      }
    },
    onJobComplete: (event) => {
      if (event.kind === 'generate_course_image') {
        clearActiveJob(setActiveImageJobIds, event.id)
        void refetchCourse()
      }
      if (isTopicGenerationJob(event.kind)) {
        clearActiveJob(setActiveTopicJobIds, event.id)
        void refetchTopics()
      }
    },
    onJobFail: (event) => {
      if (event.kind === 'generate_course_image') {
        clearActiveJob(setActiveImageJobIds, event.id)
      }
      if (isTopicGenerationJob(event.kind)) {
        clearActiveJob(setActiveTopicJobIds, event.id)
      }
    },
  })

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
      connected_course_ids: formData.connected_course_ids,
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
      void refetchCourse()
    } catch (err) {
      setError(err instanceof Error ? err.message : t().courseDetail.failedToUpdate)
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
        setError(err instanceof Error ? err.message : t().courseDetail.failedToDelete)
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
        setExportMessage(response.message || t().courseDetail.exportJobEnqueued)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : t().courseDetail.failedToExport)
      })
      .finally(() => {
        setIsExporting(false)
      })
  }

  // Handler for publishing a course
  const handleGenerateCourseImage = async () => {
    if (!isValidId) return
    setIsGeneratingImage(true)
    setImageGenerationError('')
    setError('')
    try {
      await courseService.generateCourseImage(courseId)
      void refetchCourse()
    } catch (err: unknown) {
      setImageGenerationError(err instanceof Error ? err.message : t().common.failedToGenerateImage)
    } finally {
      setIsGeneratingImage(false)
    }
  }

  const handlePublishCourse = () => {
    if (!isValidId) return

    setIsPublishing(true)
    setError('')

    void courseService
      .publishCourse(courseId)
      .then(() => {
        void refetchCourse()
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : t().courseDetail.failedToPublish)
      })
      .finally(() => {
        setIsPublishing(false)
      })
  }

  return (
    <div class="container mx-auto p-6">
      <Show
        when={isValidId}
        fallback={<div class="text-parchment-100">{t().courseDetail.invalidCourseId}</div>}
      >
        <Show
          when={!courseData.loading}
          fallback={
            <div class="text-parchment-200 font-serif p-4">{t().courseDetail.loadingCourse}</div>
          }
        >
          <Show
            when={courseData()}
            fallback={
              <div class="arcane-card p-6 text-center">{t().courseDetail.courseNotFound}</div>
            }
          >
            {(course) => (
              <div>
                <div class="flex flex-wrap items-center justify-between gap-y-3 gap-x-4 mb-4">
                  <A
                    href="/courses"
                    class="text-mystic-400 hover:text-mystic-300 transition-colors whitespace-nowrap"
                  >
                    ← {t().courseDetail.backToCourses}
                  </A>
                  <Show when={!isEditing()}>
                    <div class="flex flex-wrap items-center gap-2 sm:justify-end">
                      <ShareButton
                        url={`${window.location.origin}/share/courses/${String(courseId)}`}
                      />
                      <Show
                        when={auth.canModify(course().created_by) && course().status === 'hidden'}
                      >
                        <MagicButton
                          variant="secondary"
                          onClick={handlePublishCourse}
                          disabled={isPublishing()}
                          isLoading={isPublishing()}
                          loadingText={t().courseDetail.publishing}
                        >
                          {t().courseDetail.publishCourse}
                        </MagicButton>
                      </Show>
                      <Show when={auth.canModify(course().created_by)}>
                        <MagicButton
                          variant="ghost"
                          onClick={() => void handleGenerateCourseImage()}
                          isLoading={isGeneratingImage() || hasActiveImageJobs()}
                          loadingText={t().common.generating}
                        >
                          {course().image_url
                            ? t().common.regenerateImage
                            : t().common.generateImage}
                        </MagicButton>
                        <Button variant="primary" onClick={() => setIsEditing(true)}>
                          {t().courseDetail.editCourse}
                        </Button>
                        <Button variant="secondary" onClick={() => setShowDeleteConfirm(true)}>
                          {t().common.delete}
                        </Button>
                      </Show>
                      <RequireRole minRole="admin">
                        <Button
                          variant="outline"
                          onClick={handleExportCourse}
                          disabled={isExporting()}
                        >
                          {isExporting() ? t().courseDetail.exporting : t().courseDetail.export}
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

                <Show when={imageGenerationError()}>
                  <Alert variant="danger" class="mb-4">
                    {imageGenerationError()}
                  </Alert>
                </Show>

                {/* Export Success Message */}
                <Show when={exportMessage()}>
                  <Alert variant="success" class="mb-4">
                    <div class="flex flex-col gap-2">
                      <p>{exportMessage()}</p>
                      <Show when={exportJobId()}>
                        <A href={`/jobs`} class="text-mystic-400 hover:text-mystic-300 underline">
                          {t().courseDetail.viewJobStatus} →
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
                          {t().courseDetail.confirmDeletion}
                        </h2>
                        <p class="text-parchment-200 mb-6">
                          {t().courseDetail.confirmDeleteMessage}
                        </p>
                        <div class="flex justify-end gap-3">
                          <Button
                            variant="outline"
                            onClick={() => setShowDeleteConfirm(false)}
                            disabled={isDeleting()}
                          >
                            {t().common.cancel}
                          </Button>
                          <Button
                            variant="secondary"
                            onClick={handleDeleteCourse}
                            disabled={isDeleting()}
                          >
                            {isDeleting() ? t().common.deleting : t().courseDetail.deleteCourse}
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
                        <h2 class="text-xl font-semibold mb-4 text-parchment-100">
                          {t().courseDetail.editCourse}
                        </h2>
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
                  <div class="flex flex-col gap-6 md:flex-row md:items-start mb-6">
                    <Show when={course().image_url}>
                      <div class="w-full md:w-1/2 md:shrink-0">
                        <img
                          src={course().image_url ?? ''}
                          alt=""
                          width={256}
                          height={256}
                          loading="lazy"
                          class="w-full aspect-square rounded-lg border border-parchment-800/40 object-cover shadow-lg"
                        />
                      </div>
                    </Show>
                    <div class="flex flex-col gap-2 min-w-0 flex-1 md:w-1/2">
                      <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                        <h1 class="text-3xl font-display text-parchment-100">
                          {course().code}: {course().title}
                        </h1>
                        <CourseStatusBadge status={course().status} size="lg" class="self-start" />
                      </div>
                      <p class="text-base italic text-parchment-200 font-serif">
                        {course().description}
                      </p>
                    </div>
                  </div>

                  {/* Metadata Section */}
                  <MetadataInfo
                    type="course"
                    createdBy={course().student}
                    createdWith={course().created_with}
                    createdAt={course().created_at}
                    class="mb-6 pb-6 border-b border-parchment-800/30"
                  />

                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    {/* Course Details Section */}
                    <div class="arcane-card">
                      <h2 class="text-xl font-display text-parchment-100 mb-4 border-b border-parchment-800/30 pb-2">
                        {t().courseDetail.courseDetails}
                      </h2>
                      <div class="space-y-3 font-serif">
                        <p>
                          <span class="text-parchment-300">{t().courseDetail.level}:</span>{' '}
                          <span class="text-parchment-100">{course().level}</span>
                        </p>
                        <p>
                          <span class="text-parchment-300">
                            {t().courseDetail.lecturesPerWeek}:
                          </span>{' '}
                          <span class="text-parchment-100">{course().lectures_per_week}</span>
                        </p>
                        <p>
                          <span class="text-parchment-300">{t().courseDetail.totalWeeks}:</span>{' '}
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
                    <div class="flex flex-wrap items-center justify-between gap-4 mb-5">
                      <div class="flex flex-wrap items-center gap-3">
                        <h2 class="text-2xl font-display text-parchment-100">
                          {t().courseDetail.courseTopics}
                        </h2>
                      </div>
                      <Button variant="primary" class="shrink-0">
                        <A href={`/courses/${String(courseId)}/topics`}>
                          {t().courseDetail.editTopics}
                        </A>
                      </Button>
                    </div>

                    <TopicsList
                      topicsData={topicsData}
                      lecturesData={lecturesData}
                      courseId={courseId}
                      courseCode={course().code}
                      loading={topicsData.loading}
                      isGenerating={hasActiveTopicJobs()}
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
