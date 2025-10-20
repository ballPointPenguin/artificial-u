import { A } from '@solidjs/router'
import { type Component, createResource, createSignal, For, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import type { Course, CourseCreate } from '../api/types.js'
import { RequireAuth } from '../auth/RequireAuth'
import CourseForm from '../components/courses/CourseForm.jsx'
import type { CourseFormData } from '../components/courses/types.jsx'
import { Button } from '../components/ui'
import { getJobEventHub } from '../utils/job-events-hub.js'

const Courses: Component = () => {
  const [page, setPage] = createSignal(1)
  const [size] = createSignal(10)
  const [showCreateForm, setShowCreateForm] = createSignal(false)
  const [submitting, setSubmitting] = createSignal(false)
  const [formError, setFormError] = createSignal('')

  // Helper function to get student name safely
  const getStudentName = (course: Course): string => {
    const studentName = course.student?.name
    return studentName || '—'
  }

  // Helper function to get professor name safely
  const getProfessorName = (course: Course): string => {
    const professorName = course.professor?.name
    return professorName || '—'
  }

  // Helper function to get department name safely
  const getDepartmentName = (course: Course): string => {
    const departmentName = course.department?.name
    return departmentName || '—'
  }

  // Helper function to format date safely
  const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) return '—'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return '—'
    }
  }

  const [coursesData, { refetch }] = createResource(
    () => ({ page: page(), size: size() }),
    ({ page, size }) => courseService.listCourses({ page, size })
  )

  // Helper function to get pages safely
  const getPages = () => {
    const data = coursesData()
    return data ? data.pages : 1
  }

  // Helper function to check if we have courses
  const hasCourses = () => {
    const data = coursesData()
    return data && Array.isArray(data.items) && data.items.length > 0
  }

  const handlePrevPage = () => {
    if (page() > 1) {
      setPage(page() - 1)
    }
  }

  const handleNextPage = () => {
    const data = coursesData()
    if (data && data.pages > page()) {
      setPage(page() + 1)
    }
  }

  const handleSubmitCreate = async (formData: CourseFormData) => {
    setSubmitting(true)
    setFormError('')

    const createPayload: CourseCreate = {
      ...formData,
      // Assuming CourseForm validation ensures these are numbers when onSubmit is called
      department_id: formData.department_id as number,
      professor_id: formData.professor_id as number,
      credits: formData.credits === null ? undefined : formData.credits,
      lectures_per_week:
        formData.lectures_per_week === null ? undefined : Number(formData.lectures_per_week),
      total_weeks: formData.total_weeks === null ? undefined : Number(formData.total_weeks),
    }

    try {
      // Enqueue smart course creation job
      const job = await courseService.enqueueCreateCourse(createPayload)

      // Subscribe to SSE for create_course events and react when done/failed
      const hub = getJobEventHub()
      const unsubscribe = hub.subscribe({ kinds: ['create_course'] }, (ev) => {
        if (ev.id !== job.id) return
        if (ev.status === 'done') {
          // Refresh list and close form
          setShowCreateForm(false)
          void refetch()
          unsubscribe()
          setSubmitting(false)
        } else if (ev.status === 'failed' || ev.status === 'cancelled') {
          setFormError(ev.last_error || 'Course creation failed')
          unsubscribe()
          setSubmitting(false)
        }
      })
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Failed to enqueue course creation')
      setSubmitting(false)
    }
  }

  return (
    <div class="container mx-auto p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-display text-parchment-100 mb-6">Academic Courses</h1>
        <RequireAuth>
          <Button variant="primary" onClick={() => setShowCreateForm(true)}>
            Add Course
          </Button>
        </RequireAuth>
      </div>

      <Show when={showCreateForm()}>
        <RequireAuth>
          <div class="arcane-card p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4 text-parchment-100">Create New Course</h2>
            <CourseForm
              onSubmit={handleSubmitCreate}
              onCancel={() => setShowCreateForm(false)}
              isSubmitting={submitting()}
              error={formError()}
            />
          </div>
        </RequireAuth>
      </Show>

      <Show
        when={!coursesData.loading}
        fallback={<div class="text-parchment-200 font-serif p-4">Loading courses...</div>}
      >
        <Show
          when={hasCourses()}
          fallback={<div class="arcane-card p-6 text-center">No courses found.</div>}
        >
          <div class="arcane-card mb-6">
            <table class="min-w-full">
              <thead>
                <tr class="border-b border-parchment-800/30">
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Code
                  </th>
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Title
                  </th>
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Teacher
                  </th>
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Department
                  </th>
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Creator
                  </th>
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Last Update
                  </th>
                </tr>
              </thead>
              <tbody>
                <For each={coursesData()?.items}>
                  {(course: Course) => (
                    <tr class="border-b border-parchment-800/20 hover:bg-arcanum-800/50 transition-colors">
                      <td class="py-3 px-4 align-middle text-parchment-100">{course.code}</td>
                      <td class="py-3 px-4 align-middle text-parchment-100">
                        <A
                          href={`/courses/${String(course.id)}`}
                          class="text-parchment-100 hover:text-mystic-300 transition-colors"
                        >
                          {course.title}
                        </A>
                      </td>
                      <td class="py-3 px-4 align-middle text-parchment-100">
                        {getProfessorName(course)}
                      </td>
                      <td class="py-3 px-4 align-middle text-parchment-100">
                        {getDepartmentName(course)}
                      </td>
                      <td class="py-3 px-4 align-middle text-parchment-100">
                        {getStudentName(course)}
                      </td>
                      <td class="py-3 px-4 align-middle text-parchment-100">
                        {formatDate(course.updated_at)}
                      </td>
                    </tr>
                  )}
                </For>
              </tbody>
            </table>
          </div>

          {/* Pagination controls */}
          <Show when={getPages() > 1}>
            <div class="flex justify-between items-center mt-6">
              <div class="font-serif text-parchment-300">
                Page {page()} of {getPages()}
              </div>
              <div class="flex space-x-3">
                <Button variant="outline" onClick={handlePrevPage} disabled={page() <= 1}>
                  Previous
                </Button>
                <Button variant="outline" onClick={handleNextPage} disabled={page() >= getPages()}>
                  Next
                </Button>
              </div>
            </div>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default Courses
