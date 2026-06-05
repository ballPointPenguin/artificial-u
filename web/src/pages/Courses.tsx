import { A, useNavigate, useSearchParams } from '@solidjs/router'
import { type Component, createResource, createSignal, For, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { departmentService } from '../api/services/department-service.js'
import type { Course, CourseCreate } from '../api/types.js'
import { useAuth } from '../auth/AuthProvider'
import { RequireRole } from '../auth/RequireRole'
import CourseForm from '../components/courses/CourseForm.jsx'
import CourseStatusBadge from '../components/courses/CourseStatusBadge.jsx'
import type { CourseFormData } from '../components/courses/types.jsx'
import { Alert, Button, MagicButton } from '../components/ui'
import type { SelectOption } from '../components/ui/Select.jsx'
import Select from '../components/ui/Select.jsx'
import { useContentLanguage, useTranslations } from '../i18n'
import { createJobPolling, registerJobHandoff } from '../utils/job-management.js'

type SortField =
  | 'code'
  | 'title'
  | 'level'
  | 'status'
  | 'updated_at'
  | 'created_at'
  | 'professor'
  | 'department'
  | 'creator'
  | 'audio_count'
type SortOrder = 'asc' | 'desc'

const VALID_SORT_FIELDS: readonly SortField[] = [
  'code',
  'title',
  'level',
  'status',
  'updated_at',
  'created_at',
  'professor',
  'department',
  'creator',
  'audio_count',
]

const DEFAULT_SORT_FIELD: SortField = 'updated_at'
const DEFAULT_SORT_ORDER: SortOrder = 'desc'

const Courses: Component = () => {
  const t = useTranslations()
  const { contentLanguage } = useContentLanguage()
  const auth = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // ---------------------------------------------------------------------------
  // URL-backed state (source of truth: location query string). This means that
  // navigating back, reloading the page, or copying the URL preserves sort,
  // filter, and page state. Using URL params (rather than localStorage) keeps
  // the state scoped to this tab so independent tabs can hold independent
  // views.
  // ---------------------------------------------------------------------------
  const readStr = (key: string): string | undefined => {
    const v = searchParams[key]
    return Array.isArray(v) ? v[0] : v
  }

  const page = (): number => {
    const n = Number(readStr('page'))
    return Number.isFinite(n) && n > 0 ? Math.floor(n) : 1
  }

  const sortBy = (): SortField => {
    const v = readStr('sort_by') ?? DEFAULT_SORT_FIELD
    return (VALID_SORT_FIELDS as readonly string[]).includes(v)
      ? (v as SortField)
      : DEFAULT_SORT_FIELD
  }

  const order = (): SortOrder => (readStr('order') === 'asc' ? 'asc' : 'desc')

  const departmentFilter = (): number | null => {
    const n = Number(readStr('department_id'))
    return Number.isFinite(n) && n > 0 ? n : null
  }

  const myCoursesOnly = (): boolean => readStr('mine') === '1'

  const showHidden = (): boolean => readStr('hidden') === '1'

  // Updater helpers - `null`/`undefined`/`''` clear the param (solid-router).
  const setPage = (nextPage: number) => {
    setSearchParams({ page: nextPage > 1 ? String(nextPage) : null })
  }

  const setSort = (nextField: SortField, nextOrder: SortOrder) => {
    setSearchParams({
      sort_by: nextField === DEFAULT_SORT_FIELD ? null : nextField,
      order: nextOrder === DEFAULT_SORT_ORDER ? null : nextOrder,
      page: null,
    })
  }

  const setDepartmentFilter = (id: number | null) => {
    setSearchParams({
      department_id: id && id > 0 ? String(id) : null,
      page: null,
    })
  }

  const setMyCoursesOnly = (enabled: boolean) => {
    setSearchParams({ mine: enabled ? '1' : null, page: null })
  }

  const setShowHidden = (enabled: boolean) => {
    setSearchParams({ hidden: enabled ? '1' : null, page: null })
  }

  const [size] = createSignal(10)
  const [showCreateForm, setShowCreateForm] = createSignal(false)
  const [submitting, setSubmitting] = createSignal(false)
  const [formError, setFormError] = createSignal('')
  const [createCourseJobId, setCreateCourseJobId] = createSignal<number | null>(null)
  const [isGeneratingCourseImageId, setIsGeneratingCourseImageId] = createSignal<number | null>(
    null
  )
  const [courseImageError, setCourseImageError] = createSignal('')

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
    departmentService.listDepartments({ page: 1, size: 100, language: contentLanguage() })
  )

  // Department options for Select component
  const departmentOptions = (): SelectOption[] => {
    const depts = departmentsData()?.items || []
    // Sort departments alphabetically by name
    const sortedDepts = [...depts].sort((a, b) => a.name.localeCompare(b.name))
    return [
      { value: 0, label: t().courses.allDepartments },
      ...sortedDepts.map((dept) => ({
        value: dept.id,
        label: dept.name,
      })),
    ]
  }

  const [coursesData, { refetch, mutate: mutateCourses }] = createResource(
    () => ({
      page: page(),
      size: size(),
      sortBy: sortBy(),
      order: order(),
      departmentId: departmentFilter(),
      createdBy: myCoursesOnly() ? auth.student()?.id : undefined,
      includeHidden: showHidden(),
      language: contentLanguage(),
    }),
    ({ page, size, sortBy, order, departmentId, createdBy, includeHidden, language }) =>
      courseService.listCourses({
        page,
        size,
        sortBy,
        order,
        departmentId: departmentId || undefined,
        createdBy,
        includeHidden,
        language,
      })
  )

  createJobPolling(() => createCourseJobId(), {
    onJobComplete: (job) => {
      setShowCreateForm(false)
      setSubmitting(false)
      setCreateCourseJobId(null)

      const createdCourseId =
        job.result && typeof job.result === 'object' && 'course_id' in job.result
          ? Number((job.result as { course_id?: unknown }).course_id)
          : Number.NaN
      const topicsJobId =
        job.result && typeof job.result === 'object' && 'topics_job_id' in job.result
          ? Number((job.result as { topics_job_id?: unknown }).topics_job_id)
          : Number.NaN

      if (Number.isFinite(createdCourseId)) {
        registerJobHandoff({
          entity: { type: 'course', id: createdCourseId },
          parentJobIds: [job.id],
          jobIds: Number.isFinite(topicsJobId) ? [topicsJobId] : [],
          kinds: [
            'create_course',
            'generate_course_image',
            'generate_topics_for_course',
            'generate_topic_for_course_slot',
          ],
          expiresAt: Date.now() + 10 * 60_000,
        })
        navigate(`/courses/${String(createdCourseId)}`)
        return
      }

      void refetch()
    },
    onJobFail: (job) => {
      setFormError(job.last_error || t().courses.courseCreationFailed)
      setSubmitting(false)
      setCreateCourseJobId(null)
    },
  })

  const sortFieldOptions: SelectOption[] = [
    { value: 'updated_at', label: t().courses.lastUpdate },
    { value: 'created_at', label: t().courses.created },
    { value: 'code', label: t().courses.code },
    { value: 'title', label: t().courses.courseTitle },
    { value: 'level', label: t().courses.level },
    { value: 'status', label: t().courses.status },
    { value: 'professor', label: t().courses.teacher },
    { value: 'department', label: t().courses.department },
    { value: 'creator', label: t().courses.creator },
    { value: 'audio_count', label: t().courses.audioFiles },
  ]

  // Handle sorting - if clicking same column, toggle order; otherwise set new
  // column with sensible default direction (desc for dates/counts, asc for
  // text-y columns).
  const textSortFields: readonly SortField[] = [
    'code',
    'title',
    'level',
    'status',
    'professor',
    'department',
    'creator',
  ]

  const handleSort = (field: SortField) => {
    if (sortBy() === field) {
      setSort(field, order() === 'asc' ? 'desc' : 'asc')
    } else {
      const nextOrder: SortOrder = (textSortFields as readonly string[]).includes(field)
        ? 'asc'
        : 'desc'
      setSort(field, nextOrder)
    }
  }

  const handleMobileSortFieldChange = (value: SelectOption['value'] | null) => {
    if (value) {
      const field = value as SortField
      if ((VALID_SORT_FIELDS as readonly string[]).includes(field)) {
        setSort(field, order())
      }
    }
  }

  const toggleSortOrder = () => {
    setSort(sortBy(), order() === 'asc' ? 'desc' : 'asc')
  }

  // Handle department filter change
  const handleDepartmentFilterChange = (value: number | string | null) => {
    const deptId = typeof value === 'number' ? value : null
    setDepartmentFilter(deptId === 0 ? null : deptId)
  }

  // Sortable column header button (shared between a `th` and the mobile
  // controls). Uses the same visual affordance so users know every column is
  // sortable.
  const SortableHeader: Component<{ field: SortField; label: string; thClass?: string }> = (
    props
  ) => {
    const isActive = () => sortBy() === props.field
    const currentOrder = () => (isActive() ? order() : null)

    return (
      <th
        class={`py-3 px-3 align-middle text-left font-display text-parchment-200 whitespace-nowrap ${props.thClass ?? ''}`}
      >
        <button
          type="button"
          onClick={() => {
            handleSort(props.field)
          }}
          aria-sort={isActive() ? (currentOrder() === 'asc' ? 'ascending' : 'descending') : 'none'}
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

  // Pagination controls rendered both above and below the table so users
  // don't have to scroll to find Next/Previous.
  const Pagination: Component<{ position: 'top' | 'bottom' }> = (props) => (
    <Show when={getPages() > 1}>
      <div
        class={`flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between ${
          props.position === 'top' ? 'mb-4' : 'mt-6'
        }`}
      >
        <div class="font-serif text-parchment-300">
          {t().common.page} {page()} {t().common.of} {getPages()}
        </div>
        <div class="flex gap-3 sm:justify-end">
          <Button
            variant="outline"
            onClick={handlePrevPage}
            disabled={page() <= 1}
            aria-label={t().common.previous}
          >
            {t().common.previous}
          </Button>
          <Button
            variant="outline"
            onClick={handleNextPage}
            disabled={page() >= getPages()}
            aria-label={t().common.next}
          >
            {t().common.next}
          </Button>
        </div>
      </div>
    </Show>
  )

  const handleSubmitCreate = async (formData: CourseFormData) => {
    setSubmitting(true)
    setFormError('')
    setCreateCourseJobId(null)

    const createPayload: CourseCreate = {
      code: formData.code,
      title: formData.title,
      department_id: formData.department_id ?? undefined,
      connected_course_ids: formData.connected_course_ids,
      level: formData.level ?? undefined,
      professor_id: formData.professor_id ?? undefined,
      description: formData.description,
      lectures_per_week: formData.lectures_per_week ?? undefined,
      total_weeks: formData.total_weeks ?? undefined,
      created_with: formData.created_with ?? undefined,
      language: contentLanguage(),
    }

    try {
      // Enqueue smart course creation job
      const job = await courseService.enqueueCreateCourse(createPayload)
      setCreateCourseJobId(job.id)
    } catch (error) {
      setFormError(error instanceof Error ? error.message : t().courses.failedToEnqueue)
      setSubmitting(false)
      setCreateCourseJobId(null)
    }
  }

  const handleGenerateCourseImage = async (courseId: number) => {
    setCourseImageError('')
    setIsGeneratingCourseImageId(courseId)
    try {
      const updatedCourse = await courseService.generateCourseImage(courseId)
      // Patch the updated course into the existing list instead of doing a
      // full refetch. This keeps scroll position, avoids a loading flash, and
      // lets the new thumbnail fade in gracefully next to its neighbors.
      mutateCourses((data) => {
        if (!data) return data
        return {
          ...data,
          items: data.items.map((c) =>
            c.id === courseId
              ? {
                  ...c,
                  image_url: updatedCourse.image_url,
                  image_created_with: updatedCourse.image_created_with,
                  updated_at: updatedCourse.updated_at,
                }
              : c
          ),
        }
      })
    } catch (error) {
      setCourseImageError(error instanceof Error ? error.message : t().common.failedToGenerateImage)
    } finally {
      setIsGeneratingCourseImageId(null)
    }
  }

  const CourseThumb: Component<{ course: Course; size: 'sm' | 'md' }> = (props) => {
    const courseId = () => props.course.id
    const hasImage = () => Boolean(props.course.image_url)
    const canGenerate = () => auth.canModify(props.course.created_by)
    const isLoading = () => isGeneratingCourseImageId() === courseId()

    const boxClass = () =>
      props.size === 'sm' ? 'h-14 w-14 rounded-md' : 'h-36 w-36 shrink-0 rounded-2xl'

    const imgClass = () =>
      props.size === 'sm'
        ? 'h-14 w-14 rounded-md object-cover border border-parchment-800/30 shadow'
        : 'h-36 w-36 shrink-0 rounded-2xl object-cover border border-parchment-800/30 shadow-xl'

    const placeholderClass = () =>
      props.size === 'sm'
        ? 'h-14 w-14 rounded-md bg-parchment-900/40 border border-parchment-800/30'
        : 'h-36 w-36 shrink-0 rounded-2xl bg-parchment-900/40 border border-parchment-800/30'

    // Tracks whether the <img> has fully decoded so we can fade it in over
    // the placeholder (avoids the harsh pop when a newly-generated thumbnail
    // swaps in after `handleGenerateCourseImage`).
    const [imgLoaded, setImgLoaded] = createSignal(false)

    // Deliberately flat control flow: always render one of three branches so
    // the `<td>` can never end up visually empty, regardless of auth timing
    // or missing data.
    return (
      <Show
        when={hasImage()}
        fallback={
          <Show
            when={canGenerate()}
            fallback={
              <A href={`/courses/${String(courseId())}`} class="block">
                <div class={placeholderClass()} aria-hidden />
                <span class="sr-only">{t().courses.courseImage}</span>
              </A>
            }
          >
            <MagicButton
              type="button"
              variant="ghost"
              size="sm"
              iconOnly
              class={`${boxClass()} p-0 flex items-center justify-center`}
              aria-label={t().common.generateImage}
              title={t().common.generateImage}
              disabled={isLoading()}
              onClick={() => void handleGenerateCourseImage(courseId())}
            >
              {t().common.generateImage}
            </MagicButton>
          </Show>
        }
      >
        <A href={`/courses/${String(courseId())}`} class={`block relative ${boxClass()}`}>
          {/* Placeholder sits under the image so the slot is never empty,
              even while the browser is still decoding. */}
          <div class={`absolute inset-0 ${placeholderClass()}`} aria-hidden />
          <img
            src={props.course.image_url ?? ''}
            alt=""
            width={props.size === 'sm' ? 56 : 144}
            height={props.size === 'sm' ? 56 : 144}
            loading="lazy"
            decoding="async"
            onLoad={() => setImgLoaded(true)}
            onError={() => setImgLoaded(false)}
            class={`${imgClass()} relative transition-opacity duration-500 ${imgLoaded() ? 'opacity-100' : 'opacity-0'}`}
          />
        </A>
      </Show>
    )
  }

  return (
    <div class="container mx-auto px-4 py-6 sm:px-6">
      <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 class="text-3xl font-display text-parchment-100">{t().courses.title}</h1>
        <RequireRole minRole="creator">
          <Button variant="primary" onClick={() => setShowCreateForm(true)}>
            {t().courses.addCourse}
          </Button>
        </RequireRole>
      </div>

      <Show when={showCreateForm()}>
        <RequireRole minRole="creator">
          <div class="arcane-card p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4 text-parchment-100">
              {t().courses.createNewCourse}
            </h2>
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
        when={coursesData() !== undefined}
        fallback={<div class="text-parchment-200 font-serif p-4">{t().courses.loading}</div>}
      >
        <Show when={courseImageError()}>
          <Alert variant="danger" class="mb-4">
            {courseImageError()}
          </Alert>
        </Show>
        {/* Filter section */}
        <div class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center">
          <div class="w-full max-w-xs sm:max-w-sm lg:w-64">
            <Select
              name="department-filter"
              label={t().courses.filterByDepartment}
              value={departmentFilter() || 0}
              onChange={handleDepartmentFilterChange}
              options={departmentOptions()}
              placeholder={t().courses.allDepartments}
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
                {t().courses.clearFilter}
              </button>
            </Show>
            <Show when={auth.isAuthenticated()}>
              <label class="flex items-center gap-2 cursor-pointer text-parchment-200 transition-colors hover:text-parchment-100">
                <input
                  type="checkbox"
                  checked={myCoursesOnly()}
                  onChange={(e) => {
                    setMyCoursesOnly(e.currentTarget.checked)
                  }}
                  class="h-4 w-4 rounded border-parchment-600 bg-arcanum-900 text-mystic-500 focus:ring-mystic-500 focus:ring-offset-arcanum-900"
                />
                <span class="font-serif text-sm">{t().courses.myCourses}</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer text-parchment-200 transition-colors hover:text-parchment-100">
                <input
                  type="checkbox"
                  checked={showHidden()}
                  onChange={(e) => {
                    setShowHidden(e.currentTarget.checked)
                  }}
                  class="h-4 w-4 rounded border-parchment-600 bg-arcanum-900 text-mystic-500 focus:ring-mystic-500 focus:ring-offset-arcanum-900"
                />
                <span class="font-serif text-sm">{t().courses.hiddenCourses}</span>
              </label>
            </Show>
          </div>
          <div class="flex flex-col gap-3 lg:hidden">
            <Select
              name="sort-field"
              label={t().courses.sortField}
              value={sortBy()}
              onChange={handleMobileSortFieldChange}
              options={sortFieldOptions}
              placeholder={t().courses.sortBy}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={toggleSortOrder}
              class="self-start"
            >
              {t().courses.order}:{' '}
              {order() === 'asc' ? t().common.ascending : t().common.descending}
            </Button>
          </div>
        </div>

        <Show
          when={hasCourses()}
          fallback={<div class="arcane-card p-6 text-center">{t().courses.noCoursesFound}</div>}
        >
          {/* Top pagination mirror so users can page without scrolling past
              large result sets */}
          <div class="hidden lg:block">
            <Pagination position="top" />
          </div>

          <div class="arcane-card mb-6 hidden lg:block overflow-x-auto">
            <table class="min-w-full">
              <thead>
                <tr class="border-b border-parchment-800/30">
                  <th class="py-3 px-2 w-20 align-middle text-left font-display text-parchment-200">
                    <span class="sr-only">{t().courses.courseImage}</span>
                  </th>
                  <SortableHeader field="code" label={t().courses.code} />
                  <SortableHeader field="title" label={t().courses.courseTitle} />
                  <SortableHeader field="status" label={t().courses.status} />
                  <SortableHeader field="professor" label={t().courses.teacher} />
                  <SortableHeader field="department" label={t().courses.department} />
                  <SortableHeader field="creator" label={t().courses.creator} />
                  <SortableHeader field="updated_at" label={t().courses.lastUpdate} />
                  <SortableHeader field="audio_count" label={t().courses.audioFiles} />
                </tr>
              </thead>
              <tbody>
                <For each={coursesData()?.items}>
                  {(course: Course) => (
                    <tr class="border-b border-parchment-800/20 hover:bg-arcanum-800/50 transition-colors">
                      <td class="py-3 px-2 align-middle w-20">
                        <CourseThumb course={course} size="sm" />
                      </td>
                      <td class="py-3 px-3 align-middle text-parchment-100 whitespace-nowrap">
                        {course.code}
                      </td>
                      <td class="py-3 px-3 align-middle text-parchment-100">
                        <A
                          href={`/courses/${String(course.id)}`}
                          class="text-parchment-100 hover:text-mystic-300 transition-colors"
                        >
                          {course.title}
                        </A>
                      </td>
                      <td class="py-3 px-3 align-middle">
                        <CourseStatusBadge status={course.status} />
                      </td>
                      <td class="py-3 px-3 align-middle text-parchment-100 whitespace-nowrap">
                        {getProfessorName(course)}
                      </td>
                      <td class="py-3 px-3 align-middle text-parchment-100 whitespace-nowrap">
                        {getDepartmentName(course)}
                      </td>
                      <td class="py-3 px-3 align-middle text-parchment-100 whitespace-nowrap">
                        {getStudentName(course)}
                      </td>
                      <td class="py-3 px-3 align-middle text-parchment-100 whitespace-nowrap">
                        {formatDate(course.updated_at)}
                      </td>
                      <td class="py-3 px-3 align-middle text-parchment-100 whitespace-nowrap tabular-nums">
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
                    <div class="flex items-start justify-between gap-3">
                      <div class="min-w-0">
                        <div class="flex flex-wrap items-center gap-2">
                          <p class="text-xs font-serif uppercase tracking-wide text-parchment-400">
                            {course.code}
                          </p>
                          <CourseStatusBadge status={course.status} size="sm" />
                        </div>
                      </div>
                      <div class="shrink-0 text-xs font-serif text-parchment-400 text-right whitespace-nowrap">
                        <span class="block uppercase tracking-wide">{t().courses.updated}</span>
                        <span class="text-parchment-200">{formatDate(course.updated_at)}</span>
                      </div>
                    </div>

                    <div class="flex flex-col gap-4 min-[420px]:flex-row min-[420px]:items-start">
                      <CourseThumb course={course} size="md" />
                      <A
                        href={`/courses/${String(course.id)}`}
                        class="block min-w-0 flex-1 text-lg font-display text-parchment-100 leading-tight hover:text-mystic-300 transition-colors"
                      >
                        {course.title}
                      </A>
                    </div>
                    <div class="grid gap-3 text-sm font-serif text-parchment-200">
                      <div>
                        <span class="block text-xs uppercase tracking-wide text-parchment-500">
                          {t().courses.teacher}
                        </span>
                        <span class="text-parchment-100">{getProfessorName(course)}</span>
                      </div>
                      <div>
                        <span class="block text-xs uppercase tracking-wide text-parchment-500">
                          {t().courses.department}
                        </span>
                        <span class="text-parchment-100">{getDepartmentName(course)}</span>
                      </div>
                      <div>
                        <span class="block text-xs uppercase tracking-wide text-parchment-500">
                          {t().courses.creator}
                        </span>
                        <span class="text-parchment-100">{getStudentName(course)}</span>
                      </div>
                      <div class="flex items-center justify-between text-parchment-100">
                        <span class="text-xs uppercase tracking-wide text-parchment-500">
                          {t().courses.audioCoverage}
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
                        {t().courses.viewCourse}
                      </A>
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>

          {/* Bottom pagination */}
          <Pagination position="bottom" />
        </Show>
      </Show>
    </div>
  )
}

export default Courses
