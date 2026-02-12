import { A, useSearchParams } from '@solidjs/router'
import { type Component, createResource, createSignal, For, type JSX, Show } from 'solid-js'
import { searchService } from '../api/services/index.js'
import type {
  CourseSearchResult,
  DepartmentSearchResult,
  LectureSearchResult,
  ProfessorSearchResult,
  SearchResponse,
  TopicSearchResult,
} from '../api/types.js'
import { useI18n } from '../i18n/index.js'

function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins)}:${String(secs).padStart(2, '0')}`
}

const Search: Component = () => {
  const { t } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()

  // Extract query param as a plain string
  const queryParam = (): string | undefined => {
    const raw = searchParams.q
    if (Array.isArray(raw)) return raw[0]
    return raw
  }

  // Local input state, initialized from URL
  const [inputValue, setInputValue] = createSignal(queryParam() ?? '')

  // Fetch results when query param changes
  const [results] = createResource<SearchResponse | null, string | undefined>(
    queryParam,
    async (q) => {
      if (!q || q.length < 2) return null
      return searchService.search({ q })
    }
  )

  const handleSubmit = (e: Event) => {
    e.preventDefault()
    const q = inputValue().trim()
    if (q.length >= 2) {
      setSearchParams({ q })
    }
  }

  const totalResults = () => {
    const r = results()
    if (!r) return 0
    return (
      r.lectures.length +
      r.courses.length +
      r.professors.length +
      r.departments.length +
      r.topics.length
    )
  }

  return (
    <div class="max-w-5xl mx-auto px-6 py-12">
      {/* Search bar */}
      <form onSubmit={handleSubmit} class="mb-10">
        <div class="flex gap-3">
          <div class="relative flex-1">
            <svg
              class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted pointer-events-none"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="search"
              value={inputValue()}
              onInput={(e) => {
                setInputValue(e.currentTarget.value)
              }}
              placeholder={t().search.placeholder}
              class="arcane-input w-full pl-12 pr-4 py-3 text-base"
              autofocus
            />
          </div>
          <button
            type="submit"
            class="bg-primary text-background px-6 py-3 rounded font-sans text-sm uppercase tracking-wider hover:opacity-90 transition-opacity"
          >
            {t().search.viewAll === 'View all' ? 'Search' : t().search.viewAll}
          </button>
        </div>
      </form>

      {/* Loading state */}
      <Show when={results.loading}>
        <div class="text-center text-muted py-12">
          <div class="animate-pulse space-y-4 max-w-2xl mx-auto">
            <div class="h-5 bg-border/50 rounded w-1/3 mx-auto" />
            <div class="h-4 bg-border/30 rounded w-2/3 mx-auto" />
            <div class="h-4 bg-border/30 rounded w-1/2 mx-auto" />
          </div>
        </div>
      </Show>

      {/* Results */}
      <Show when={!results.loading && results()}>
        {(r) => (
          <>
            {/* Results header */}
            <div class="mb-8 border-b border-border pb-4">
              <h1 class="text-2xl font-display text-foreground">
                {t().search.resultsFor} <span class="text-primary">"{r().query}"</span>
              </h1>
              <p class="text-sm text-muted mt-1">
                {totalResults()} result{totalResults() !== 1 ? 's' : ''}
              </p>
            </div>

            {/* No results */}
            <Show when={totalResults() === 0}>
              <p class="text-muted text-center py-12">{t().search.noResults}</p>
            </Show>

            {/* Lectures */}
            <Show when={r().lectures.length > 0}>
              <ResultSection title={t().search.lectures}>
                <For each={r().lectures}>
                  {(lec: LectureSearchResult) => (
                    <A
                      href={`/courses/${String(lec.course_id)}/lectures/${String(lec.id)}`}
                      class="block bg-surface border border-border rounded-lg p-5 card-hover-lift"
                    >
                      <h4 class="font-display text-foreground mb-1">{lec.title}</h4>
                      <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                        <Show when={lec.course_code}>
                          <span>{lec.course_code}</span>
                        </Show>
                        <Show when={lec.professor_name}>
                          <span>{lec.professor_name}</span>
                        </Show>
                        <Show when={lec.department_name}>
                          <span class="tag-teal">{lec.department_name}</span>
                        </Show>
                        <Show when={lec.duration}>
                          <span>{formatDuration(lec.duration)}</span>
                        </Show>
                      </div>
                      <Show when={lec.summary}>
                        <p class="text-sm text-muted mt-2 line-clamp-2">{lec.summary}</p>
                      </Show>
                    </A>
                  )}
                </For>
              </ResultSection>
            </Show>

            {/* Courses */}
            <Show when={r().courses.length > 0}>
              <ResultSection title={t().search.courses}>
                <For each={r().courses}>
                  {(course: CourseSearchResult) => (
                    <A
                      href={`/courses/${String(course.id)}`}
                      class="block bg-surface border border-border rounded-lg p-5 card-hover-lift"
                    >
                      <div class="flex items-baseline gap-2 mb-1">
                        <span class="font-sans text-xs text-primary font-medium">
                          {course.code}
                        </span>
                        <h4 class="font-display text-foreground">{course.title}</h4>
                      </div>
                      <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                        <Show when={course.professor_name}>
                          <span>{course.professor_name}</span>
                        </Show>
                        <Show when={course.department_name}>
                          <span class="tag-teal">{course.department_name}</span>
                        </Show>
                        <Show when={course.level}>
                          <span>{course.level}</span>
                        </Show>
                      </div>
                      <Show when={course.description}>
                        <p class="text-sm text-muted mt-2 line-clamp-2">{course.description}</p>
                      </Show>
                    </A>
                  )}
                </For>
              </ResultSection>
            </Show>

            {/* Professors */}
            <Show when={r().professors.length > 0}>
              <ResultSection title={t().search.professors}>
                <For each={r().professors}>
                  {(prof: ProfessorSearchResult) => (
                    <A
                      href={`/professors/${String(prof.id)}`}
                      class="block bg-surface border border-border rounded-lg p-5 card-hover-lift"
                    >
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-full bg-secondary/20 border border-secondary/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
                          <Show
                            when={prof.image_url}
                            fallback={
                              <span class="font-sans text-xs font-semibold text-secondary">
                                {prof.name
                                  .split(' ')
                                  .map((n) => n[0])
                                  .join('')
                                  .slice(0, 2)
                                  .toUpperCase()}
                              </span>
                            }
                          >
                            <img
                              src={prof.image_url!}
                              alt={prof.name}
                              class="w-10 h-10 rounded-full object-cover"
                            />
                          </Show>
                        </div>
                        <div class="min-w-0">
                          <h4 class="font-display text-foreground">{prof.name}</h4>
                          <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                            <Show when={prof.title}>
                              <span>{prof.title}</span>
                            </Show>
                            <Show when={prof.department_name}>
                              <span class="tag-teal">{prof.department_name}</span>
                            </Show>
                          </div>
                          <Show when={prof.specialization}>
                            <p class="text-sm text-muted mt-1 line-clamp-1">
                              {prof.specialization}
                            </p>
                          </Show>
                        </div>
                      </div>
                    </A>
                  )}
                </For>
              </ResultSection>
            </Show>

            {/* Departments */}
            <Show when={r().departments.length > 0}>
              <ResultSection title={t().search.departments}>
                <For each={r().departments}>
                  {(dept: DepartmentSearchResult) => (
                    <A
                      href={`/departments/${String(dept.id)}`}
                      class="block bg-surface border border-border rounded-lg p-5 card-hover-lift"
                    >
                      <div class="flex items-baseline gap-2 mb-1">
                        <span class="font-sans text-xs text-primary font-medium">{dept.code}</span>
                        <h4 class="font-display text-foreground">{dept.name}</h4>
                      </div>
                      <Show when={dept.description}>
                        <p class="text-sm text-muted mt-1 line-clamp-2">{dept.description}</p>
                      </Show>
                    </A>
                  )}
                </For>
              </ResultSection>
            </Show>

            {/* Topics */}
            <Show when={r().topics.length > 0}>
              <ResultSection title={t().search.topics}>
                <For each={r().topics}>
                  {(topic: TopicSearchResult) => (
                    <A
                      href={`/courses/${String(topic.course_id)}/topics/${String(topic.id)}`}
                      class="block bg-surface border border-border rounded-lg p-5 card-hover-lift"
                    >
                      <h4 class="font-display text-foreground mb-1">
                        Week {String(topic.week)}: {topic.title}
                      </h4>
                      <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                        <Show when={topic.course_code}>
                          <span>{topic.course_code}</span>
                        </Show>
                        <Show when={topic.course_title}>
                          <span>{topic.course_title}</span>
                        </Show>
                      </div>
                    </A>
                  )}
                </For>
              </ResultSection>
            </Show>
          </>
        )}
      </Show>

      {/* Empty state - no query yet */}
      <Show when={!results.loading && results() === undefined && !searchParams.q}>
        <div class="text-center py-16">
          <svg
            class="w-16 h-16 text-border mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p class="text-muted">{t().search.placeholder}</p>
        </div>
      </Show>
    </div>
  )
}

/** Simple section wrapper with a heading */
const ResultSection: Component<{ title: string; children: JSX.Element }> = (props) => {
  return (
    <div class="mb-10">
      <h2 class="section-label mb-4">{props.title}</h2>
      <div class="grid gap-3">{props.children}</div>
    </div>
  )
}

export default Search
