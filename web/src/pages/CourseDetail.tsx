import { A, useNavigate, useParams } from '@solidjs/router'
import { type Component, For, Show, createResource, createSignal } from 'solid-js'
import {
  deleteCourse,
  getCourse,
  getCourseDepartment,
  getCourseLectures,
  getCourseProfessor,
  updateCourse,
} from '../api/services/course-service'
import type { LectureBrief, LecturesList } from '../api/types'
import CourseForm, { type CourseFormData } from '../components/courses/CourseForm'
import { Button } from '../components/ui/Button'

const CourseDetail: Component = () => {
  const params = useParams()
  const navigate = useNavigate()
  // Ensure params.id exists and is a valid number string before parsing
  const courseId = params.id ? Number.parseInt(params.id, 10) : Number.NaN

  // State for edit mode and form submission
  const [isEditing, setIsEditing] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')
  const [showDeleteConfirm, setShowDeleteConfirm] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)

  // Check if courseId is a valid number before creating resources
  const isValidId = !Number.isNaN(courseId)

  const [courseData, { refetch }] = createResource(
    () => (isValidId ? courseId : null), // Pass null if ID is invalid
    getCourse
  )
  const [professorData] = createResource(() => (isValidId ? courseId : null), getCourseProfessor)
  const [departmentData] = createResource(() => (isValidId ? courseId : null), getCourseDepartment)
  const [lecturesData] = createResource(() => (isValidId ? courseId : null), getCourseLectures)

  // Helper function to safely check if lectures exist
  const hasLectures = () => {
    const data = lecturesData()
    return data && Array.isArray(data.lectures) && data.lectures.length > 0
  }

  // Handler for course update form submission
  const handleUpdateCourse = async (formData: CourseFormData) => {
    if (!isValidId) return

    setIsSubmitting(true)
    setError('')

    try {
      await updateCourse(courseId, formData)
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

    void deleteCourse(courseId)
      .then(() => {
        // Redirect to courses list after successful deletion
        navigate('/academics/courses')
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to delete course')
        setShowDeleteConfirm(false)
      })
      .finally(() => {
        setIsDeleting(false)
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
                    href="/academics/courses"
                    class="text-mystic-400 hover:text-mystic-300 transition-colors"
                  >
                    ← Back to Courses
                  </A>
                  <Show when={!isEditing()}>
                    <div class="flex gap-2">
                      <Button variant="primary" onClick={() => setIsEditing(true)}>
                        Edit Course
                      </Button>
                      <Button variant="secondary" onClick={() => setShowDeleteConfirm(true)}>
                        Delete
                      </Button>
                    </div>
                  </Show>
                </div>

                {/* Delete Confirmation Dialog */}
                <Show when={showDeleteConfirm()}>
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
                </Show>

                <Show
                  when={!isEditing()}
                  fallback={
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
                  }
                >
                  <h1 class="text-3xl font-display text-parchment-100 mb-3">
                    {course().code}: {course().title}
                  </h1>
                  <p class="text-xl text-parchment-200 mb-6 font-serif">{course().description}</p>

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
                          <span class="text-parchment-300">Credits:</span>{' '}
                          <span class="text-parchment-100">{course().credits}</span>
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
                      {/* Department Info */}
                      <div class="arcane-card">
                        <h2 class="text-xl font-display text-parchment-100 mb-4 border-b border-parchment-800/30 pb-2">
                          Department
                        </h2>
                        <Show
                          when={!departmentData.loading}
                          fallback={
                            <div class="text-parchment-400 font-serif">Loading department...</div>
                          }
                        >
                          <Show
                            when={departmentData()}
                            fallback={
                              <div class="text-parchment-400 font-serif">
                                Department info not available.
                              </div>
                            }
                          >
                            {(dept) => {
                              const department = dept()
                              return (
                                <div class="font-serif">
                                  <A
                                    href={`/academics/departments/${String(department.id)}`}
                                    class="text-mystic-400 hover:text-mystic-300 transition-colors font-medium"
                                  >
                                    {department.name} ({department.code})
                                  </A>
                                  <p class="text-parchment-300 mt-1">
                                    Faculty: {department.faculty}
                                  </p>
                                </div>
                              )
                            }}
                          </Show>
                        </Show>
                      </div>

                      {/* Professor Info */}
                      <div class="arcane-card">
                        <h2 class="text-xl font-display text-parchment-100 mb-4 border-b border-parchment-800/30 pb-2">
                          Professor
                        </h2>
                        <Show
                          when={!professorData.loading}
                          fallback={
                            <div class="text-parchment-400 font-serif">Loading professor...</div>
                          }
                        >
                          <Show
                            when={professorData()}
                            fallback={
                              <div class="text-parchment-400 font-serif">
                                Professor info not available.
                              </div>
                            }
                          >
                            {(prof) => {
                              const professor = prof()
                              return (
                                <div class="font-serif">
                                  <A
                                    href={`/academics/professors/${String(professor.id)}`}
                                    class="text-mystic-400 hover:text-mystic-300 transition-colors font-medium"
                                  >
                                    {professor.name}
                                  </A>
                                  <p class="text-parchment-300 mt-1">{professor.title}</p>
                                  <p class="text-parchment-400 mt-2 text-sm">
                                    Specialization: {professor.specialization}
                                  </p>
                                </div>
                              )
                            }}
                          </Show>
                        </Show>
                      </div>
                    </div>
                  </div>

                  {/* Lectures Section */}
                  <div class="mt-8">
                    <h2 class="text-2xl font-display text-parchment-100 mb-5">Course Lectures</h2>
                    <Show
                      when={!lecturesData.loading}
                      fallback={
                        <div class="text-parchment-200 font-serif p-4">Loading lectures...</div>
                      }
                    >
                      <Show
                        when={hasLectures()}
                        fallback={
                          <div class="arcane-card p-6 text-center text-parchment-400 font-serif">
                            No lectures found for this course.
                          </div>
                        }
                      >
                        <ul class="space-y-4">
                          <For each={(lecturesData() as LecturesList).lectures}>
                            {(lecture: LectureBrief) => (
                              <li class="arcane-card hover:shadow-arcane transition-all">
                                <h3 class="text-lg font-display text-parchment-100 mb-2">
                                  Week {lecture.week_number}.{lecture.order_in_week}:{' '}
                                  {lecture.title}
                                </h3>
                                <p class="text-parchment-300 font-serif mb-3">
                                  {lecture.description}
                                </p>
                                {lecture.audio_url && (
                                  <div class="mt-4">
                                    <audio controls src={lecture.audio_url} class="w-full">
                                      <track kind="captions" />
                                      Your browser does not support the audio element.
                                    </audio>
                                  </div>
                                )}
                              </li>
                            )}
                          </For>
                        </ul>
                      </Show>
                    </Show>
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
