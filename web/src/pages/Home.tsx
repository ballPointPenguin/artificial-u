import { A, useNavigate } from '@solidjs/router'
import { createResource, createSignal, For, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { departmentService } from '../api/services/department-service.js'
import { featuredService } from '../api/services/featured-service.js'
import { lectureService } from '../api/services/lecture-service.js'
import { professorService } from '../api/services/professor-service.js'
import type {
  Department,
  FeaturedItem,
  PlatformStats,
  Professor,
  RecentLecture,
} from '../api/types.js'
import { FeaturedLectureCarousel } from '../components/FeaturedLectureCarousel.jsx'
import { Button } from '../components/ui'
import { useContentLanguage, useTranslations } from '../i18n'

const Home = () => {
  const t = useTranslations()
  const { contentLanguage } = useContentLanguage()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = createSignal('')

  const handleSearch = (e: Event) => {
    e.preventDefault()
    const q = searchQuery().trim()
    if (q.length >= 2) {
      navigate(`/search?q=${encodeURIComponent(q)}`)
    }
  }

  // Fetch live stats
  const [stats] = createResource<PlatformStats>(() => featuredService.getStats())

  // Fetch featured lectures (for hero carousel) — enriched via /recent?ids=...
  const [heroLectures] = createResource(
    () => contentLanguage(),
    async (lang) => {
      const items: FeaturedItem[] = await featuredService.listFeatured({
        item_type: 'lecture',
        language: lang,
      })
      if (items.length === 0) return [] as RecentLecture[]

      // Fetch enriched data for the specific featured lecture IDs
      const ids = items.map((i) => i.item_id)
      const enriched = await lectureService.getRecentLectures(ids)

      // Re-order to match the admin-configured display_order
      const byId = new Map(enriched.map((l) => [l.id, l]))
      return ids.map((id) => byId.get(id)).filter((l): l is RecentLecture => l != null)
    }
  )

  // Fetch recently added published courses (for the grid section)
  const [recentCourses] = createResource(
    () => contentLanguage(),
    async (lang) => {
      const result = await courseService.listCourses({
        page: 1,
        size: 8,
        sortBy: 'created_at',
        order: 'desc',
        language: lang,
      })
      return result.items.filter((c) => c.status === 'published').slice(0, 4)
    }
  )

  // Fetch featured professors
  const [featuredProfessors] = createResource(
    () => contentLanguage(),
    async (lang) => {
      const items: FeaturedItem[] = await featuredService.listFeatured({
        item_type: 'professor',
        language: lang,
      })
      if (items.length === 0) return [] as Professor[]

      const professors = await Promise.all(
        items.map(async (item) => {
          try {
            return await professorService.getProfessor(item.item_id)
          } catch {
            return null
          }
        })
      )
      return professors.filter((p): p is Professor => p !== null)
    }
  )

  // Fetch featured departments
  const [featuredDepartments] = createResource(
    () => contentLanguage(),
    async (lang) => {
      const items: FeaturedItem[] = await featuredService.listFeatured({
        item_type: 'department',
        language: lang,
      })
      if (items.length === 0) return [] as Department[]

      const departments = await Promise.all(
        items.map(async (item) => {
          try {
            return await departmentService.getDepartment(item.item_id)
          } catch {
            return null
          }
        })
      )
      return departments.filter((d): d is Department => d !== null)
    }
  )

  return (
    <div>
      {/* ─── Hero Section ─── */}
      <section class="relative px-6 md:px-12 lg:px-16 py-16 md:py-24 overflow-hidden">
        {/* Subtle radial gradients */}
        <div class="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div
            class="absolute inset-0"
            style={{
              background:
                'radial-gradient(ellipse at 20% 50%, hsl(var(--theme-secondary-h) var(--theme-secondary-s) var(--theme-secondary-l) / 0.06) 0%, transparent 60%), radial-gradient(ellipse at 80% 30%, hsl(var(--theme-primary-h) var(--theme-primary-s) var(--theme-primary-l) / 0.04) 0%, transparent 50%)',
            }}
          />
        </div>

        <div class="relative z-10 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: headline + CTAs */}
          <div>
            <h1 class="font-display text-3xl sm:text-4xl md:text-5xl font-normal leading-tight text-foreground mb-5">
              {t().home.hero.titleStart}
              <em class="text-primary not-italic">{t().home.hero.titleEmphasis}</em>
              {t().home.hero.titleEnd}
            </h1>
            <p class="text-lg text-muted max-w-lg mb-8 leading-relaxed">{t().home.hero.subtitle}</p>
            <div class="flex flex-wrap gap-4">
              <A href="/browse">
                <Button variant="primary" size="lg">
                  <span class="mr-2">&#9654;</span>
                  {t().home.hero.browseCta}
                </Button>
              </A>
              <A href="/quickstart">
                <Button variant="outline" size="lg">
                  {t().home.hero.createCta}
                </Button>
              </A>
            </div>
          </div>

          {/* Right: featured lecture carousel */}
          <div>
            <Show
              when={heroLectures() && heroLectures()!.length > 0}
              fallback={
                <div class="bg-surface border border-border rounded-lg p-6 lg:max-w-md lg:ml-auto">
                  <div class="section-label mb-4">{t().home.featuredLectures.nowPlaying}</div>
                  <div class="space-y-3 animate-pulse">
                    <div class="h-5 bg-border/50 rounded w-3/4" />
                    <div class="h-4 bg-border/30 rounded w-full" />
                    <div class="h-4 bg-border/30 rounded w-1/2" />
                    <div class="flex items-center gap-3 mt-4">
                      <div class="w-10 h-10 rounded-full bg-border/40" />
                      <div class="space-y-1.5 flex-1">
                        <div class="h-3.5 bg-border/30 rounded w-1/2" />
                        <div class="h-3 bg-border/20 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
              }
            >
              <FeaturedLectureCarousel
                lectures={heroLectures()!}
                label={t().home.featuredLectures.nowPlaying}
              />
            </Show>
          </div>
        </div>
      </section>

      {/* ─── Stats Strip ─── */}
      <section class="border-y border-border/50 py-10">
        <div class="max-w-4xl mx-auto flex flex-wrap justify-center gap-8 md:gap-16 items-center">
          <Show
            when={stats()}
            fallback={
              <div class="flex gap-16">
                <div class="text-center animate-pulse">
                  <div class="h-10 w-16 bg-border/30 rounded mx-auto mb-1" />
                  <div class="h-4 w-20 bg-border/20 rounded mx-auto" />
                </div>
                <div class="text-center animate-pulse">
                  <div class="h-10 w-16 bg-border/30 rounded mx-auto mb-1" />
                  <div class="h-4 w-20 bg-border/20 rounded mx-auto" />
                </div>
                <div class="text-center animate-pulse">
                  <div class="h-10 w-16 bg-border/30 rounded mx-auto mb-1" />
                  <div class="h-4 w-20 bg-border/20 rounded mx-auto" />
                </div>
              </div>
            }
          >
            {(s) => (
              <>
                <div class="text-center">
                  <div class="stat-number">{s().course_count}</div>
                  <div class="text-sm font-sans text-muted uppercase tracking-widest mt-1">
                    {t().home.stats.courses}
                  </div>
                </div>
                <div class="hidden md:block w-px h-12 bg-border/40" />
                <div class="text-center">
                  <div class="stat-number">{s().lecture_count}</div>
                  <div class="text-sm font-sans text-muted uppercase tracking-widest mt-1">
                    {t().home.stats.lectures}
                  </div>
                </div>
                <div class="hidden md:block w-px h-12 bg-border/40" />
                <div class="text-center">
                  <div class="stat-number">{s().audio_hours}</div>
                  <div class="text-sm font-sans text-muted uppercase tracking-widest mt-1">
                    {t().home.stats.audioHours}
                  </div>
                </div>
              </>
            )}
          </Show>
        </div>
      </section>

      {/* ─── Recently Added Courses ─── */}
      <Show when={(recentCourses() ?? []).length > 0}>
        <section class="py-16 px-6 md:px-12 lg:px-16">
          <div class="max-w-7xl mx-auto">
            <div class="flex items-center justify-between mb-8">
              <div>
                <span class="section-label">New arrivals</span>
                <h2 class="text-2xl font-display text-foreground">Recently Added Courses</h2>
              </div>
              <A
                href="/browse"
                class="text-sm font-sans text-accent hover:text-primary transition-colors"
              >
                View all courses &rarr;
              </A>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <For each={recentCourses()}>
                {(course) => (
                  <A
                    href={`/courses/${String(course.id)}`}
                    class="card-hover-lift rounded-lg border border-border bg-surface p-4 flex flex-col no-underline text-inherit"
                  >
                    {/* Department tag */}
                    <Show when={course.department?.name}>
                      <span class="tag-teal inline-block rounded px-2 py-0.5 text-xs font-sans font-medium mb-2 self-start">
                        {course.department!.name}
                      </span>
                    </Show>

                    {/* Title */}
                    <h4 class="font-display text-foreground text-base mb-2 leading-snug flex-1">
                      {course.title}
                    </h4>

                    {/* Professor row */}
                    <Show when={course.professor}>
                      <div class="flex items-center gap-2 mt-auto pt-2 border-t border-border/40">
                        <div class="w-7 h-7 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
                          <Show
                            when={course.professor!.image_url}
                            fallback={
                              <span class="font-sans text-xs font-semibold text-primary">
                                {course
                                  .professor!.name.split(' ')
                                  .map((n: string) => n[0])
                                  .join('')
                                  .slice(0, 2)}
                              </span>
                            }
                          >
                            <img
                              src={course.professor!.image_url!}
                              alt={course.professor!.name}
                              class="w-7 h-7 rounded-full object-cover"
                            />
                          </Show>
                        </div>
                        <span class="text-xs text-muted truncate">{course.professor!.name}</span>
                      </div>
                    </Show>
                  </A>
                )}
              </For>
            </div>
          </div>
        </section>
      </Show>

      {/* ─── Featured Departments ─── */}
      <Show when={(featuredDepartments() ?? []).length > 0}>
        <section class="py-16 px-6 md:px-12 lg:px-16 bg-surface-alt">
          <div class="max-w-7xl mx-auto">
            <div class="flex items-center justify-between mb-8">
              <div>
                <span class="section-label">Explore</span>
                <h2 class="text-2xl font-display text-foreground">Browse Departments</h2>
              </div>
              <A
                href="/academics"
                class="text-sm font-sans text-accent hover:text-primary transition-colors"
              >
                All departments &rarr;
              </A>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <For each={featuredDepartments()}>
                {(dept) => (
                  <A
                    href={`/departments/${String(dept.id)}`}
                    class="card-hover-lift rounded-lg border border-border bg-surface p-5 block no-underline text-inherit"
                  >
                    <h4 class="font-display text-foreground text-lg mb-1">{dept.name}</h4>
                    <p class="text-sm text-muted line-clamp-2">
                      {dept.description ? dept.description.slice(0, 120) : ''}
                    </p>
                  </A>
                )}
              </For>
            </div>
          </div>
        </section>
      </Show>

      {/* ─── Professor Spotlight ─── */}
      <Show when={(featuredProfessors() ?? []).length > 0}>
        <section class="py-16 px-6 md:px-12 lg:px-16">
          <div class="max-w-7xl mx-auto">
            <div class="flex items-center justify-between mb-8">
              <div>
                <span class="section-label">Meet the faculty</span>
                <h2 class="text-2xl font-display text-foreground">Professor Spotlight</h2>
              </div>
              <A
                href="/professors"
                class="text-sm font-sans text-accent hover:text-primary transition-colors"
              >
                All professors &rarr;
              </A>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <For each={featuredProfessors()}>
                {(prof) => (
                  <A
                    href={`/professors/${String(prof.id)}`}
                    class="card-hover-lift rounded-lg border border-border bg-surface p-5 flex gap-4 items-start no-underline text-inherit"
                  >
                    <div class="w-12 h-12 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
                      <Show
                        when={prof.image_url}
                        fallback={
                          <span class="font-sans text-sm font-semibold text-primary">
                            {prof.name
                              .split(' ')
                              .map((n) => n[0])
                              .join('')
                              .slice(0, 2)}
                          </span>
                        }
                      >
                        <img
                          src={prof.image_url!}
                          alt={prof.name}
                          class="w-12 h-12 rounded-full object-cover"
                        />
                      </Show>
                    </div>
                    <div>
                      <h4 class="font-display text-foreground text-base">{prof.name}</h4>
                      <Show when={prof.specialization}>
                        <p class="text-sm text-muted">
                          {prof.specialization!.length > 150
                            ? `${prof.specialization!.slice(0, 150)}…`
                            : prof.specialization}
                        </p>
                      </Show>
                      <Show when={prof.title}>
                        <p class="text-xs text-muted mt-1">{prof.title}</p>
                      </Show>
                    </div>
                  </A>
                )}
              </For>
            </div>
          </div>
        </section>
      </Show>

      {/* ─── Search ─── */}
      <section class="px-6 md:px-12 lg:px-16 py-12 bg-surface-alt">
        <div class="max-w-3xl mx-auto">
          <form onSubmit={handleSearch} class="flex gap-3">
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
                value={searchQuery()}
                onInput={(e) => {
                  setSearchQuery(e.currentTarget.value)
                }}
                placeholder={t().search.placeholder}
                class="arcane-input w-full pl-12 pr-4 py-3 text-base"
              />
            </div>
            <button
              type="submit"
              class="bg-primary text-background px-6 py-3 rounded font-sans text-sm uppercase tracking-wider hover:opacity-90 transition-opacity flex-shrink-0"
            >
              Search
            </button>
          </form>
        </div>
      </section>

      {/* ─── CTA Banner ─── */}
      <section class="px-6 md:px-12 lg:px-16 py-16">
        <div class="cta-banner max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-8 lg:gap-12 items-center">
          <div>
            <h2 class="text-2xl md:text-3xl font-display text-foreground mb-3">
              {t().home.ctaBanner.title}
            </h2>
            <p class="text-muted leading-relaxed max-w-xl mb-4">{t().home.ctaBanner.description}</p>
            <div class="flex flex-wrap gap-x-6 gap-y-2 text-xs font-sans text-muted">
              <span class="before:content-['✦_'] before:text-primary/60">
                {t().home.ctaBanner.feature1}
              </span>
              <span class="before:content-['✦_'] before:text-primary/60">
                {t().home.ctaBanner.feature2}
              </span>
              <span class="before:content-['✦_'] before:text-primary/60">
                {t().home.ctaBanner.feature3}
              </span>
            </div>
          </div>
          <div class="flex flex-col items-start lg:items-center gap-3">
            <A href="/quickstart">
              <Button variant="primary" size="lg">
                {t().home.ctaBanner.cta}
              </Button>
            </A>
            <span class="text-xs font-sans text-muted">{t().home.ctaBanner.priceHint}</span>
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section class="px-6 md:px-12 lg:px-16 py-16 bg-surface-alt">
        <div class="max-w-7xl mx-auto">
          <div class="mb-10">
            <div class="section-label">{t().home.howItWorks.sectionLabel}</div>
            <h2 class="text-3xl md:text-4xl font-display text-foreground">
              {t().home.howItWorks.title}
            </h2>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <div class="relative bg-surface border border-border rounded-lg p-7">
              <span class="absolute top-4 right-5 font-display text-5xl font-bold text-border/60 leading-none select-none">
                1
              </span>
              <h3 class="font-display text-lg font-semibold text-primary mb-2">
                {t().home.howItWorks.step1Title}
              </h3>
              <p class="text-sm text-muted leading-relaxed">{t().home.howItWorks.step1Desc}</p>
            </div>

            {/* Step 2 */}
            <div class="relative bg-surface border border-border rounded-lg p-7">
              <span class="absolute top-4 right-5 font-display text-5xl font-bold text-border/60 leading-none select-none">
                2
              </span>
              <h3 class="font-display text-lg font-semibold text-primary mb-2">
                {t().home.howItWorks.step2Title}
              </h3>
              <p class="text-sm text-muted leading-relaxed">{t().home.howItWorks.step2Desc}</p>
            </div>

            {/* Step 3 */}
            <div class="relative bg-surface border border-border rounded-lg p-7">
              <span class="absolute top-4 right-5 font-display text-5xl font-bold text-border/60 leading-none select-none">
                3
              </span>
              <h3 class="font-display text-lg font-semibold text-primary mb-2">
                {t().home.howItWorks.step3Title}
              </h3>
              <p class="text-sm text-muted leading-relaxed">{t().home.howItWorks.step3Desc}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Trust & Transparency ─── */}
      <section class="px-6 md:px-12 lg:px-16 py-16">
        <div class="max-w-7xl mx-auto">
          <div class="mb-10">
            <div class="section-label">{t().home.trust.sectionLabel}</div>
            <h2 class="text-3xl md:text-4xl font-display text-foreground">
              {t().home.trust.title}
            </h2>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* AI Transparency */}
            <div class="bg-surface border border-border rounded-lg p-7 card-hover-lift flex flex-col">
              <div class="text-3xl mb-4" aria-hidden="true">
                🤖
              </div>
              <h3 class="font-display text-lg text-foreground mb-2">{t().home.trust.aiTitle}</h3>
              <p class="text-sm text-muted leading-relaxed mb-4 flex-1">{t().home.trust.aiDesc}</p>
              <A href="/about/ai-ethics" class="text-sm text-primary hover:underline">
                {t().home.trust.aiLink}
              </A>
            </div>

            {/* Privacy First */}
            <div class="bg-surface border border-border rounded-lg p-7 card-hover-lift flex flex-col">
              <div class="text-3xl mb-4" aria-hidden="true">
                🔒
              </div>
              <h3 class="font-display text-lg text-foreground mb-2">
                {t().home.trust.privacyTitle}
              </h3>
              <p class="text-sm text-muted leading-relaxed mb-4 flex-1">
                {t().home.trust.privacyDesc}
              </p>
              <A href="/about/privacy" class="text-sm text-primary hover:underline">
                {t().home.trust.privacyLink}
              </A>
            </div>

            {/* Not a Replacement */}
            <div class="bg-surface border border-border rounded-lg p-7 card-hover-lift flex flex-col">
              <div class="text-3xl mb-4" aria-hidden="true">
                📜
              </div>
              <h3 class="font-display text-lg text-foreground mb-2">
                {t().home.trust.notReplacementTitle}
              </h3>
              <p class="text-sm text-muted leading-relaxed mb-4 flex-1">
                {t().home.trust.notReplacementDesc}
              </p>
              <A href="/about/terms" class="text-sm text-primary hover:underline">
                {t().home.trust.notReplacementLink}
              </A>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home
