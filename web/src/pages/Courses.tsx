import { A } from '@solidjs/router'
import { type Component, For, Show, createResource, createSignal } from 'solid-js'
import { createCourse, getCourses } from '../api/services/course-service'
import type { Course, CoursesList } from '../api/types'
import CourseForm, { type CourseFormData } from '../components/courses/CourseForm'
import { Button } from '../components/ui/Button'

const Courses: Component = () => {
  const [page, setPage] = createSignal(1)
  const [size] = createSignal(10)
  const [showCreateForm, setShowCreateForm] = createSignal(false)
  const [submitting, setSubmitting] = createSignal(false)
  const [formError, setFormError] = createSignal('')

  const [coursesData, { refetch }] = createResource(
    () => ({ page: page(), size: size() }),
    ({ page, size }) => getCourses({ page, size })
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

    try {
      await createCourse(formData)
      setShowCreateForm(false)
      void refetch()
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Failed to create course')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div class="container mx-auto p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-display text-parchment-100 mb-6">Academic Courses</h1>
        <Button variant="primary" onClick={() => setShowCreateForm(true)}>
          Add Course
        </Button>
      </div>

      <Show when={showCreateForm()}>
        <div class="arcane-card p-6 mb-8">
          <h2 class="text-xl font-semibold mb-4 text-parchment-100">Create New Course</h2>
          <CourseForm
            onSubmit={handleSubmitCreate}
            onCancel={() => setShowCreateForm(false)}
            isSubmitting={submitting()}
            error={formError()}
          />
        </div>
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
                  <th class="py-3 px-4 text-left font-display text-parchment-200">Code</th>
                  <th class="py-3 px-4 text-left font-display text-parchment-200">Title</th>
                  <th class="py-3 px-4 text-left font-display text-parchment-200">Level</th>
                  <th class="py-3 px-4 text-left font-display text-parchment-200">Credits</th>
                  <th class="py-3 px-4 text-left font-display text-parchment-200">Actions</th>
                </tr>
              </thead>
              <tbody>
                <For each={(coursesData() as CoursesList).items}>
                  {(course: Course) => (
                    <tr class="border-b border-parchment-800/20 hover:bg-arcanum-800/50 transition-colors">
                      <td class="py-3 px-4 text-parchment-100">{course.code}</td>
                      <td class="py-3 px-4 text-parchment-100">{course.title}</td>
                      <td class="py-3 px-4 text-parchment-100">{course.level}</td>
                      <td class="py-3 px-4 text-parchment-100">{course.credits}</td>
                      <td class="py-3 px-4">
                        <A
                          href={`/academics/courses/${String(course.id)}`}
                          class="text-mystic-400 hover:text-mystic-300 transition-colors"
                        >
                          View Details
                        </A>
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
                <button
                  type="button"
                  class="px-4 py-2"
                  onClick={handlePrevPage}
                  disabled={page() <= 1}
                >
                  Previous
                </button>
                <button
                  type="button"
                  class="px-4 py-2"
                  onClick={handleNextPage}
                  disabled={page() >= getPages()}
                >
                  Next
                </button>
              </div>
            </div>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default Courses
