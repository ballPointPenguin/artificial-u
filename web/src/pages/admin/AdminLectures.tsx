import { A, useSearchParams } from '@solidjs/router'
import { type Component, createResource, For, Show } from 'solid-js'
import { lectureService } from '../../api/services/lecture-service'
import type { AdminLectureListItem } from '../../api/types'
import { Button } from '../../components/ui'
import { formatDate } from '../../utils/formatDate'

type SortField =
  | 'title'
  | 'revision'
  | 'course_id'
  | 'course_code'
  | 'topic_id'
  | 'lecture_id'
  | 'voice_id'
  | 'audio'
  | 'timeline'
  | 'images'
  | 'created_at'
  | 'updated_at'
type SortOrder = 'asc' | 'desc'

const VALID_SORT_FIELDS: readonly SortField[] = [
  'title',
  'revision',
  'course_id',
  'course_code',
  'topic_id',
  'lecture_id',
  'voice_id',
  'audio',
  'timeline',
  'images',
  'created_at',
  'updated_at',
]

const DEFAULT_SORT_FIELD: SortField = 'lecture_id'
const DEFAULT_SORT_ORDER: SortOrder = 'desc'
const PAGE_SIZE = 25
const TITLE_LENGTH = 40

const truncateTitle = (title: string): string =>
  title.length > TITLE_LENGTH ? `${title.slice(0, TITLE_LENGTH)}…` : title

const formatTimestamp = (timestamp: unknown): string => {
  if (typeof timestamp !== 'string' || !timestamp) return '-'
  const date = new Date(timestamp)
  return Number.isNaN(date.getTime()) ? '-' : formatDate(date)
}

const YesNoBadge: Component<{ value: boolean }> = (props) => (
  <span
    class={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
      props.value
        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200'
        : 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300'
    }`}
  >
    {props.value ? 'Yes' : 'No'}
  </span>
)

export default function AdminLectures() {
  const [searchParams, setSearchParams] = useSearchParams()

  const readStr = (key: string): string | undefined => {
    const value = searchParams[key]
    return Array.isArray(value) ? value[0] : value
  }

  const page = (): number => {
    const value = Number(readStr('page'))
    return Number.isFinite(value) && value > 0 ? Math.floor(value) : 1
  }

  const courseIdFilter = (): number | null => {
    const value = Number(readStr('course_id'))
    return Number.isFinite(value) && value > 0 ? Math.floor(value) : null
  }

  const courseCodeFilter = (): string => readStr('course_code') ?? ''

  const sortBy = (): SortField => {
    const value = readStr('sort_by') ?? DEFAULT_SORT_FIELD
    return (VALID_SORT_FIELDS as readonly string[]).includes(value)
      ? (value as SortField)
      : DEFAULT_SORT_FIELD
  }

  const order = (): SortOrder => (readStr('order') === 'asc' ? 'asc' : 'desc')

  const setPage = (nextPage: number) => {
    setSearchParams({ page: nextPage > 1 ? String(nextPage) : null })
  }

  const setCourseIdFilter = (value: string) => {
    const courseId = Number(value)
    setSearchParams({
      course_id: Number.isFinite(courseId) && courseId > 0 ? String(Math.floor(courseId)) : null,
      page: null,
    })
  }

  const setCourseCodeFilter = (value: string) => {
    const trimmed = value.trim()
    setSearchParams({ course_code: trimmed ? trimmed : null, page: null })
  }

  const setSort = (field: SortField, nextOrder: SortOrder) => {
    setSearchParams({
      sort_by: field === DEFAULT_SORT_FIELD ? null : field,
      order: nextOrder === DEFAULT_SORT_ORDER ? null : nextOrder,
      page: null,
    })
  }

  const handleSort = (field: SortField) => {
    if (sortBy() === field) {
      setSort(field, order() === 'asc' ? 'desc' : 'asc')
      return
    }

    const textFields: readonly SortField[] = ['title', 'course_code']
    setSort(field, (textFields as readonly string[]).includes(field) ? 'asc' : 'desc')
  }

  const [lecturesData, { refetch }] = createResource(
    () => ({
      page: page(),
      courseId: courseIdFilter(),
      courseCode: courseCodeFilter(),
      sortBy: sortBy(),
      order: order(),
    }),
    ({ page: currentPage, courseId, courseCode, sortBy: currentSortBy, order: currentOrder }) =>
      lectureService.listAdminLectures({
        page: currentPage,
        size: PAGE_SIZE,
        courseId: courseId ?? undefined,
        courseCode: courseCode || undefined,
        sortBy: currentSortBy,
        order: currentOrder,
      })
  )

  const totalPages = () => lecturesData()?.pages ?? 1
  const hasLectures = () => (lecturesData()?.items.length ?? 0) > 0

  const handlePrevPage = () => {
    if (page() > 1) setPage(page() - 1)
  }

  const handleNextPage = () => {
    if (page() < totalPages()) setPage(page() + 1)
  }

  const clearFilters = () => {
    setSearchParams({ course_id: null, course_code: null, page: null })
  }

  const imageStatus = (lecture: AdminLectureListItem): string => {
    if (!lecture.images_timeline_url) return 'No'
    if (lecture.image_slots_done !== null && lecture.image_slots_total !== null) {
      return `${String(lecture.image_slots_done)}/${String(lecture.image_slots_total)}`
    }
    return lecture.image_slots_error ? 'Error' : 'Yes'
  }

  const SortableHeader: Component<{ field: SortField; label: string }> = (props) => {
    const isActive = () => sortBy() === props.field
    const currentOrder = () => (isActive() ? order() : null)

    return (
      <th class="py-3 px-3 align-middle text-left font-display text-parchment-200 whitespace-nowrap">
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

  const Pagination: Component<{ position: 'top' | 'bottom' }> = (props) => (
    <Show when={totalPages() > 1}>
      <div
        class={`flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between ${
          props.position === 'top' ? 'mb-4' : 'mt-6'
        }`}
      >
        <div class="font-serif text-parchment-300">
          Page {page()} of {totalPages()}
        </div>
        <div class="flex gap-3 sm:justify-end">
          <Button variant="outline" onClick={handlePrevPage} disabled={page() <= 1}>
            Previous
          </Button>
          <Button variant="outline" onClick={handleNextPage} disabled={page() >= totalPages()}>
            Next
          </Button>
        </div>
      </div>
    </Show>
  )

  return (
    <main class="container mx-auto px-4 py-6 sm:px-6">
      <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-3xl font-display text-parchment-100">Lectures</h1>
          <p class="mt-1 font-serif text-sm text-parchment-300">
            All lecture records, including media and image timeline status.
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => {
            void refetch()
          }}
        >
          Refresh
        </Button>
      </div>

      <div class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end">
        <label class="flex w-full max-w-xs flex-col gap-2 font-serif text-sm text-parchment-200">
          Course code
          <input
            type="search"
            class="arcane-input"
            value={courseCodeFilter()}
            placeholder="e.g. REL350"
            onInput={(event) => {
              setCourseCodeFilter(event.currentTarget.value)
            }}
          />
        </label>
        <label class="flex w-full max-w-xs flex-col gap-2 font-serif text-sm text-parchment-200">
          Course ID
          <input
            type="number"
            min="1"
            class="arcane-input"
            value={courseIdFilter() ?? ''}
            placeholder="e.g. 42"
            onInput={(event) => {
              setCourseIdFilter(event.currentTarget.value)
            }}
          />
        </label>
        <Show when={courseCodeFilter() || courseIdFilter()}>
          <Button variant="ghost" onClick={clearFilters}>
            Clear Filters
          </Button>
        </Show>
      </div>

      <Show
        when={!lecturesData.loading}
        fallback={<div class="text-parchment-200 font-serif p-4">Loading lectures...</div>}
      >
        <Show
          when={!lecturesData.error}
          fallback={
            <div class="text-danger text-center py-8">
              <p>
                Error loading lectures:{' '}
                {lecturesData.error instanceof Error ? lecturesData.error.message : 'Unknown error'}
              </p>
              <Button variant="ghost" onClick={() => void refetch()} class="mt-4">
                Retry
              </Button>
            </div>
          }
        >
          <Pagination position="top" />
          <Show
            when={hasLectures()}
            fallback={<div class="arcane-card p-8 text-center">No lectures found.</div>}
          >
            <div class="arcane-card overflow-x-auto">
              <table class="min-w-full">
                <thead>
                  <tr class="border-b border-parchment-700/60">
                    <SortableHeader field="title" label="Title" />
                    <SortableHeader field="revision" label="Revision" />
                    <SortableHeader field="course_id" label="Course ID" />
                    <SortableHeader field="course_code" label="Code" />
                    <SortableHeader field="topic_id" label="Topic ID" />
                    <SortableHeader field="lecture_id" label="Lecture ID" />
                    <SortableHeader field="voice_id" label="Voice ID" />
                    <SortableHeader field="audio" label="Audio" />
                    <SortableHeader field="timeline" label="Timeline" />
                    <SortableHeader field="images" label="Images" />
                    <SortableHeader field="created_at" label="Created" />
                    <SortableHeader field="updated_at" label="Updated" />
                  </tr>
                </thead>
                <tbody>
                  <For each={lecturesData()?.items ?? []}>
                    {(lecture) => (
                      <tr class="border-b border-parchment-800/40 transition-colors hover:bg-muted/30">
                        <td class="px-3 py-4 font-serif text-sm">
                          <A
                            href={`/courses/${String(lecture.course_id)}/lectures/${String(lecture.id)}`}
                            class="text-primary transition-colors hover:text-primary/80"
                            title={lecture.title}
                          >
                            {truncateTitle(lecture.title)}
                          </A>
                        </td>
                        <td class="px-3 py-4 whitespace-nowrap text-sm">
                          {lecture.revision ?? '-'}
                        </td>
                        <td class="px-3 py-4 whitespace-nowrap text-sm">{lecture.course_id}</td>
                        <td class="px-3 py-4 whitespace-nowrap text-sm">
                          {lecture.course_code ?? '-'}
                        </td>
                        <td class="px-3 py-4 whitespace-nowrap text-sm">{lecture.topic_id}</td>
                        <td class="px-3 py-4 whitespace-nowrap text-sm">{lecture.id}</td>
                        <td class="px-3 py-4 whitespace-nowrap text-sm">
                          {lecture.voice_id ?? '-'}
                        </td>
                        <td class="px-3 py-4 whitespace-nowrap">
                          <YesNoBadge value={Boolean(lecture.audio_url)} />
                        </td>
                        <td class="px-3 py-4 whitespace-nowrap">
                          <YesNoBadge value={Boolean(lecture.timeline_url)} />
                        </td>
                        <td
                          class="px-3 py-4 whitespace-nowrap text-sm"
                          title={lecture.image_slots_error ?? undefined}
                        >
                          {imageStatus(lecture)}
                        </td>
                        <td class="px-3 py-4 whitespace-nowrap text-sm text-muted">
                          {formatTimestamp(lecture.created_at)}
                        </td>
                        <td class="px-3 py-4 whitespace-nowrap text-sm text-muted">
                          {formatTimestamp(lecture.updated_at)}
                        </td>
                      </tr>
                    )}
                  </For>
                </tbody>
              </table>
            </div>
          </Show>
          <Pagination position="bottom" />
        </Show>
      </Show>
    </main>
  )
}
