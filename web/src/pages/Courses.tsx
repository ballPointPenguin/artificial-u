import { A } from '@solidjs/router'
import { type Component, createResource, createSignal, For, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { departmentService } from '../api/services/department-service.js'
import type { Course, CourseCreate } from '../api/types.js'
import { useAuth } from '../auth/AuthProvider'
import { RequireRole } from '../auth/RequireRole'
import CourseForm from '../components/courses/CourseForm.jsx'
import type { CourseFormData } from '../components/courses/types.jsx'
import { Button } from '../components/ui'
import type { SelectOption } from '../components/ui/Select.jsx'
import Select from '../components/ui/Select.jsx'
import { getJobEventHub } from '../utils/job-events-hub.js'

type SortField = 'code' | 'title' | 'level' | 'credits' | 'updated_at' | 'created_at'
type SortOrder = 'asc' | 'desc'

const Courses: Component = () => {
  const auth = useAuth()
  const [page, setPage] = createSignal(1)
  const [size] = createSignal(10)
  const [sortBy, setSortBy] = createSignal<SortField>('updated_at')
  const [order, setOrder] = createSignal<SortOrder>('desc')
  const [departmentFilter, setDepartmentFilter] = createSignal<number | null>(null)
  const [myCoursesOnly, setMyCoursesOnly] = createSignal(false)
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

  // Fetch departments for filter dropdown
  const [departmentsData] = createResource(() =>
    departmentService.listDepartments({ page: 1, size: 100 })
  )

  // Department options for Select component
  const departmentOptions = (): SelectOption[] => {
    const depts = departmentsData()?.items || []
    // Sort departments alphabetically by name
    const sortedDepts = [...depts].sort((a, b) => a.name.localeCompare(b.name))
    return [
      { value: 0, label: 'All Departments' },
      ...sortedDepts.map((dept) => ({
        value: dept.id,
        label: dept.name,
      })),
    ]
  }

  const [coursesData, { refetch }] = createResource(
    () => ({
      page: page(),
      size: size(),
      sortBy: sortBy(),
      order: order(),
      departmentId: departmentFilter(),
      createdBy: myCoursesOnly() ? auth.student()?.id : undefined,
    }),
    ({ page, size, sortBy, order, departmentId, createdBy }) =>
      courseService.listCourses({
        page,
        size,
        sortBy,
        order,
        departmentId: departmentId || undefined,
        createdBy,
      })
  )

  const sortFieldOptions: SelectOption[] = [
    { value: 'updated_at', label: 'Last Update' },
    { value: 'created_at', label: 'Created' },
    { value: 'code', label: 'Code' },
    { value: 'title', label: 'Title' },
    { value: 'level', label: 'Level' },
    { value: 'credits', label: 'Credits' },
  ]

  // Handle sorting - if clicking same column, toggle order; otherwise set new column with desc
  const handleSort = (field: SortField) => {
    if (sortBy() === field) {
      // Toggle order
      setOrder(order() === 'asc' ? 'desc' : 'asc')
    } else {
      // New column, default to descending
      setSortBy(field)
      setOrder('desc')
    }
    // Reset to first page when sorting changes
    setPage(1)
  }

  const handleMobileSortFieldChange = (value: SelectOption['value'] | null) => {
    if (value) {
      setSortBy(value as SortField)
      setPage(1)
    }
  }

  const toggleSortOrder = () => {
    setOrder(order() === 'asc' ? 'desc' : 'asc')
    setPage(1)
  }

  // Handle department filter change
  const handleDepartmentFilterChange = (value: number | string | null) => {
    const deptId = typeof value === 'number' ? value : null
    setDepartmentFilter(deptId === 0 ? null : deptId)
    // Reset to first page when filter changes
    setPage(1)
  }

  // Sortable column header component
  const SortableHeader: Component<{ field: SortField; label: string }> = (props) => {
    const isActive = () => sortBy() === props.field
    const currentOrder = () => (isActive() ? order() : null)

    return (
      <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
        <button
          type="button"
          onClick={() => {
            handleSort(props.field)
          }}
          class="flex items-center gap-2 hover:text-parchment-100 transition-colors cursor-pointer select-none"
        >
          <span>{props.label}</span>
          <span class="inline-flex flex-col text-xs leading-none">
            <span
              class={
                isActive() && currentOrder() === 'asc'
                  ? 'text-mystic-300'
                  : 'text-parchment-600 opacity-50'
              }
            >
              ▲
            </span>
            <span
              class={
                isActive() && currentOrder() === 'desc'
                  ? 'text-mystic-300'
                  : 'text-parchment-600 opacity-50'
              }
            >
              ▼
            </span>
          </span>
        </button>
      </th>
    )
  }

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
      code: formData.code,
      title: formData.title,
      department_id: formData.department_id ?? undefined,
      level: formData.level ?? undefined,
      credits: formData.credits ?? undefined,
      professor_id: formData.professor_id ?? undefined,
      description: formData.description,
      lectures_per_week: formData.lectures_per_week ?? undefined,
      total_weeks: formData.total_weeks ?? undefined,
      created_with: formData.created_with ?? undefined,
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
    <div class="container mx-auto px-4 py-6 sm:px-6">
      <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 class="text-3xl font-display text-parchment-100">Academic Courses</h1>
        <RequireRole minRole="creator">
          <Button variant="primary" onClick={() => setShowCreateForm(true)}>
            Add Course
          </Button>
        </RequireRole>
      </div>

      <Show when={showCreateForm()}>
        <RequireRole minRole="creator">
          <div class="arcane-card p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4 text-parchment-100">Create New Course</h2>
            <CourseForm
              onSubmit={handleSubmitCreate}
              onCancel={() => setShowCreateForm(false)}
              isSubmitting={submitting()}
              error={formError()}
            />
          </div>
        </RequireRole>
      </Show>

      <Show
        when={!coursesData.loading}
        fallback={<div class="text-parchment-200 font-serif p-4">Loading courses...</div>}
      >
        {/* Filter section */}
        <div class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center">
          <div class="w-full max-w-xs sm:max-w-sm lg:w-64">
            <Select
              name="department-filter"
              label="Filter by Department"
              value={departmentFilter() || 0}
              onChange={handleDepartmentFilterChange}
              options={departmentOptions()}
              placeholder="All Departments"
              disabled={departmentsData.loading}
            />
          </div>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Show when={departmentFilter() !== null}>
              <button
                type="button"
                onClick={() => {
                  handleDepartmentFilterChange(0)
                }}
                class="self-start text-sm text-parchment-300 transition-colors hover:text-mystic-300"
              >
                Clear filter
              </button>
            </Show>
            <Show when={auth.isAuthenticated()}>
              <label class="flex items-center gap-2 cursor-pointer text-parchment-200 transition-colors hover:text-parchment-100">
                <input
                  type="checkbox"
                  checked={myCoursesOnly()}
                  onChange={(e) => {
                    setMyCoursesOnly(e.currentTarget.checked)
                    setPage(1) // Reset to first page when filter changes
                  }}
                  class="h-4 w-4 rounded border-parchment-600 bg-arcanum-900 text-mystic-500 focus:ring-mystic-500 focus:ring-offset-arcanum-900"
                />
                <span class="font-serif text-sm">My Courses</span>
              </label>
            </Show>
          </div>
          <div class="flex flex-col gap-3 sm:hidden">
            <Select
              name="sort-field"
              label="Sort field"
              value={sortBy()}
              onChange={handleMobileSortFieldChange}
              options={sortFieldOptions}
              placeholder="Sort by"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={toggleSortOrder}
              class="self-start"
            >
              Order: {order() === 'asc' ? 'Ascending' : 'Descending'}
            </Button>
          </div>
        </div>

        <Show
          when={hasCourses()}
          fallback={<div class="arcane-card p-6 text-center">No courses found.</div>}
        >
          <div class="arcane-card mb-6 hidden lg:block">
            <table class="min-w-full">
              <thead>
                <tr class="border-b border-parchment-800/30">
                  <SortableHeader field="code" label="Code" />
                  <SortableHeader field="title" label="Title" />
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Teacher
                  </th>
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Department
                  </th>
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Creator
                  </th>
                  <SortableHeader field="updated_at" label="Last Update" />
                  <th class="py-3 px-4 align-middle text-left font-display text-parchment-200">
                    Audio Files
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
                      <td class="py-3 px-4 align-middle text-parchment-100">
                        {course.lectures_with_audio_count ?? 0} / {course.topics_count ?? 0}
                      </td>
                    </tr>
                  )}
                </For>
              </tbody>
            </table>
          </div>

          <div class="mb-6 space-y-4 lg:hidden">
            <For each={coursesData()?.items}>
              {(course: Course) => (
                <div class="arcane-card p-4">
                  <div class="flex flex-col gap-4">
                    <div class="flex items-start justify-between gap-4">
                      <div class="flex-1">
                        <p class="text-xs font-serif uppercase tracking-wide text-parchment-400">
                          {course.code}
                        </p>
                        <A
                          href={`/courses/${String(course.id)}`}
                          class="mt-1 block text-lg font-display text-parchment-100 leading-tight hover:text-mystic-300 transition-colors"
                        >
                          {course.title}
                        </A>
                      </div>
                      <div class="text-xs font-serif text-parchment-400 text-right">
                        <span class="block uppercase tracking-wide">Updated</span>
                        <span class="text-parchment-200">{formatDate(course.updated_at)}</span>
                      </div>
                    </div>
                    <div class="grid gap-3 text-sm font-serif text-parchment-200">
                      <div>
                        <span class="block text-xs uppercase tracking-wide text-parchment-500">
                          Teacher
                        </span>
                        <span class="text-parchment-100">{getProfessorName(course)}</span>
                      </div>
                      <div>
                        <span class="block text-xs uppercase tracking-wide text-parchment-500">
                          Department
                        </span>
                        <span class="text-parchment-100">{getDepartmentName(course)}</span>
                      </div>
                      <div>
                        <span class="block text-xs uppercase tracking-wide text-parchment-500">
                          Creator
                        </span>
                        <span class="text-parchment-100">{getStudentName(course)}</span>
                      </div>
                      <div class="flex items-center justify-between text-parchment-100">
                        <span class="text-xs uppercase tracking-wide text-parchment-500">
                          Audio Coverage
                        </span>
                        <span>
                          {course.lectures_with_audio_count ?? 0} / {course.topics_count ?? 0}
                        </span>
                      </div>
                    </div>
                    <div class="flex justify-end">
                      <A
                        href={`/courses/${String(course.id)}`}
                        class="text-sm font-serif text-mystic-300 hover:text-mystic-200 transition-colors"
                      >
                        View course →
                      </A>
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>

          {/* Pagination controls */}
          <Show when={getPages() > 1}>
            <div class="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div class="font-serif text-parchment-300">
                Page {page()} of {getPages()}
              </div>
              <div class="flex gap-3 sm:justify-end">
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
