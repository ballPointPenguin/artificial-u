import { A, useSearchParams } from '@solidjs/router'
import { type Component, createResource, createSignal, For, Index, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { tagService } from '../api/services/tag-service.js'
import type { Course, TagWithCount } from '../api/types.js'
import CrateCard from '../components/browse/CrateCard.jsx'
import CrateRow from '../components/browse/CrateRow.jsx'
import SurpriseMe from '../components/browse/SurpriseMe.jsx'
import TagChipsBar from '../components/browse/TagChipsBar.jsx'
import { Alert, Button, LoadingSpinner } from '../components/ui'
import { useContentLanguage, useTranslations } from '../i18n'

const PAGE_SIZE = 24
const TAG_CHIP_LIMIT = 30
const CRATE_ROW_TAGS = 5
const CRATE_ROW_SIZE = 12

/** One horizontally scrolling crate for a single tag (unfiltered view). */
const TagCrateRow: Component<{ tag: TagWithCount; language: string }> = (props) => {
  const [coursesData] = createResource(
    () => ({ slug: props.tag.slug, language: props.language }),
    (source) =>
      courseService.listCourses({
        page: 1,
        size: CRATE_ROW_SIZE,
        language: source.language,
        tags: [source.slug],
        sortBy: 'updated_at',
      })
  )
  return (
    <CrateRow
      title={props.tag.name}
      courses={coursesData()?.items ?? []}
      loading={coursesData.loading}
    />
  )
}

const Browse: Component = () => {
  const t = useTranslations()
  const { contentLanguage } = useContentLanguage()
  const [searchParams, setSearchParams] = useSearchParams()

  // ---------------------------------------------------------------------------
  // URL-backed filter state (?tags=slug&tags=slug2) so browsing state survives
  // reloads and can be shared or linked from tag chips elsewhere in the app.
  // ---------------------------------------------------------------------------
  const selectedTags = (): string[] => {
    const value = searchParams.tags
    if (!value) return []
    return Array.isArray(value) ? value : [value]
  }

  const toggleTag = (slug: string) => {
    const current = selectedTags()
    const next = current.includes(slug) ? current.filter((s) => s !== slug) : [...current, slug]
    setSearchParams({ tags: next.length > 0 ? next : null })
    setLoadedPages(1)
  }

  const clearTags = () => {
    setSearchParams({ tags: null })
    setLoadedPages(1)
  }

  const hasFilter = () => selectedTags().length > 0

  // "Load more" appends pages to the grid instead of paginating.
  const [loadedPages, setLoadedPages] = createSignal(1)

  const [tagsData] = createResource(
    () => ({ language: contentLanguage() }),
    (source) => tagService.listTags({ language: source.language, limit: TAG_CHIP_LIMIT })
  )

  // Once a filter is active, narrow the chip options to tags that actually
  // co-occur with the current selection, so picking "Paleoclimate History"
  // won't leave dead-end chips like "Neurobiology" that would yield 0 results.
  const [narrowedTagsData] = createResource(
    () => (hasFilter() ? { language: contentLanguage(), tags: selectedTags() } : null),
    (source) =>
      tagService.listTags({ language: source.language, tags: source.tags, limit: TAG_CHIP_LIMIT })
  )

  const [recentData] = createResource(
    () => ({ language: contentLanguage() }),
    (source) =>
      courseService.listCourses({
        page: 1,
        size: CRATE_ROW_SIZE,
        language: source.language,
        sortBy: 'updated_at',
      })
  )

  // Filtered grid: accumulate pages so "Load more" appends.
  const [gridCourses, setGridCourses] = createSignal<Course[]>([])
  const [gridData] = createResource(
    () =>
      hasFilter()
        ? { language: contentLanguage(), tags: selectedTags(), pages: loadedPages() }
        : null,
    async (source) => {
      const responses = await Promise.all(
        Array.from({ length: source.pages }, (_, i) =>
          courseService.listCourses({
            page: i + 1,
            size: PAGE_SIZE,
            language: source.language,
            tags: source.tags,
            sortBy: 'updated_at',
          })
        )
      )
      const items = responses.flatMap((r) => r.items)
      setGridCourses(items)
      return { total: responses[0]?.total ?? 0, loaded: items.length }
    }
  )

  const topTags = (): TagWithCount[] => tagsData()?.items ?? []
  const crateRowTags = (): TagWithCount[] => topTags().slice(0, CRATE_ROW_TAGS)
  const canLoadMore = () => (gridData()?.loaded ?? 0) < (gridData()?.total ?? 0)

  // Chips shown in the filter bar: the full vocabulary when nothing is
  // selected, or the narrowed co-occurring set (plus any selected tags that
  // fell out of the narrowed set, e.g. a zero-result combination) once filtering.
  const chipTags = (): TagWithCount[] => {
    if (!hasFilter()) return topTags()
    const narrowed = narrowedTagsData()?.items ?? []
    const narrowedSlugs = new Set(narrowed.map((tag) => tag.slug))
    const stillSelected = selectedTags()
      .filter((slug) => !narrowedSlugs.has(slug))
      .map((slug) => topTags().find((tag) => tag.slug === slug))
      .filter((tag): tag is TagWithCount => tag !== undefined)
    return [...narrowed, ...stillSelected]
  }

  return (
    <div class="container mx-auto px-4 py-6 sm:px-6">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-3xl font-display text-parchment-100">{t().browse.title}</h1>
          <p class="mt-1 font-serif italic text-muted">{t().browse.subtitle}</p>
          <A
            href="/courses"
            class="mt-2 inline-block font-sans text-xs text-muted underline-offset-2 hover:text-primary hover:underline"
          >
            {t().browse.catalogueLink}
          </A>
        </div>
        <SurpriseMe
          language={contentLanguage()}
          tags={selectedTags()}
          label={t().browse.surpriseMe}
          loadingLabel={t().browse.picking}
        />
      </div>

      <Show when={Boolean(tagsData.error)}>
        <Alert variant="danger" class="mb-4">
          {t().browse.errorLoading}
        </Alert>
      </Show>

      <Show when={chipTags().length > 0}>
        <div class="mb-6">
          <TagChipsBar
            tags={chipTags()}
            selected={selectedTags()}
            onToggle={toggleTag}
            onClear={clearTags}
            allLabel={t().browse.all}
          />
        </div>
      </Show>

      <Show
        when={hasFilter()}
        fallback={
          <>
            <CrateRow
              title={t().browse.recentlyAdded}
              courses={recentData()?.items ?? []}
              loading={recentData.loading}
            />
            <Index each={crateRowTags()}>
              {(tag) => <TagCrateRow tag={tag()} language={contentLanguage()} />}
            </Index>
          </>
        }
      >
        <Show when={!gridData.loading || gridCourses().length > 0} fallback={<LoadingSpinner />}>
          <Show
            when={gridCourses().length > 0}
            fallback={
              <div class="flex flex-col items-start gap-3">
                <p class="font-serif text-muted">{t().browse.empty}</p>
                <Button variant="outline" onClick={clearTags}>
                  {t().browse.resetFilters}
                </Button>
              </div>
            }
          >
            <div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
              <For each={gridCourses()}>{(course) => <CrateCard course={course} />}</For>
            </div>
            <Show when={canLoadMore()}>
              <div class="mt-6 flex justify-center">
                <Button
                  variant="outline"
                  disabled={gridData.loading}
                  onClick={() => setLoadedPages((n) => n + 1)}
                >
                  {gridData.loading ? t().common.loading : t().browse.loadMore}
                </Button>
              </div>
            </Show>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default Browse
