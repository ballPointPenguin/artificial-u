import { A } from '@solidjs/router'
import { createResource, For, Show } from 'solid-js'
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
import { useTranslations } from '../i18n'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'

// Helper: format seconds as "12 min"
function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return ''
  const mins = Math.round(seconds / 60)
  return `${String(mins)} min`
}

const Home = () => {
  const t = useTranslations()
  const audioPlayer = useAudioPlayer()

  // Fetch live stats
  const [stats] = createResource<PlatformStats>(() => featuredService.getStats())

  // Fetch featured lectures (for hero carousel) — enriched via /recent?ids=...
  const [heroLectures] = createResource<RecentLecture[]>(async () => {
    const items: FeaturedItem[] = await featuredService.listFeatured({
      item_type: 'lecture',
      language: 'en',
    })
    if (items.length === 0) return []

    // Fetch enriched data for the specific featured lecture IDs
    const ids = items.map((i) => i.item_id)
    const enriched = await lectureService.getRecentLectures(ids)

    // Re-order to match the admin-configured display_order
    const byId = new Map(enriched.map((l) => [l.id, l]))
    return ids.map((id) => byId.get(id)).filter((l): l is RecentLecture => l != null)
  })

  // Fetch recent lectures (for the grid section) — purely chronological
  const [recentLectures] = createResource<RecentLecture[]>(() =>
    lectureService.getRecentLectures(4)
  )

  // Fetch featured professors
  const [featuredProfessors] = createResource<Professor[]>(async () => {
    const items: FeaturedItem[] = await featuredService.listFeatured({
      item_type: 'professor',
      language: 'en',
    })
    if (items.length === 0) return []

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
  })

  // Fetch featured departments
  const [featuredDepartments] = createResource<Department[]>(async () => {
    const items: FeaturedItem[] = await featuredService.listFeatured({
      item_type: 'department',
      language: 'en',
    })
    if (items.length === 0) return []

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
  })

  const handlePlayRecent = (lecture: RecentLecture) => {
    if (!lecture.audio_url) return
    audioPlayer.playTrack({
      url: lecture.audio_url,
      title: lecture.title,
      subtitle: lecture.course_code
        ? `${lecture.course_code}: ${lecture.course_title ?? ''}`
        : undefined,
      lectureId: lecture.id,
      courseId: lecture.course_id,
      topicId: lecture.topic_id,
      courseCode: lecture.course_code ?? undefined,
      topicWeek: lecture.topic_week ?? undefined,
    })
  }

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
              <A href="/courses">
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

      {/* ─── Recently Added Lectures ─── */}
      <Show when={(recentLectures() ?? []).length > 0}>
        <section class="py-16 px-6 md:px-12 lg:px-16">
          <div class="max-w-7xl mx-auto">
            <div class="flex items-center justify-between mb-8">
              <div>
                <span class="section-label">Listen now</span>
                <h2 class="text-2xl font-display text-foreground">Recently Added Lectures</h2>
              </div>
              <A
                href="/courses"
                class="text-sm font-sans text-accent hover:text-primary transition-colors"
              >
                View all lectures &rarr;
              </A>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <For each={recentLectures()}>
                {(lecture) => (
                  <div class="card-hover-lift rounded-lg border border-border bg-surface p-4">
                    {/* Department tag */}
                    <Show when={lecture.department_name}>
                      <span class="tag-teal inline-block rounded px-2 py-0.5 text-xs font-sans font-medium mb-2">
                        {lecture.department_name}
                      </span>
                    </Show>

                    {/* Title */}
                    <A
                      href={`/lectures/${String(lecture.id)}`}
                      class="block no-underline text-inherit"
                    >
                      <h4 class="font-display text-foreground text-base mb-1 leading-snug">
                        {lecture.title}
                      </h4>
                    </A>

                    {/* Course code + topic */}
                    <p class="text-xs text-muted mb-2">
                      <Show when={lecture.course_code}>
                        <span>{lecture.course_code}</span>
                      </Show>
                      <Show when={lecture.topic_title}>
                        <span class="mx-1">&middot;</span>
                        <span>{lecture.topic_title}</span>
                      </Show>
                    </p>

                    {/* Professor + duration row */}
                    <div class="flex items-center justify-between mt-auto">
                      <Show when={lecture.professor_name}>
                        <span class="text-xs text-muted truncate">{lecture.professor_name}</span>
                      </Show>
                      <div class="flex items-center gap-2 flex-shrink-0">
                        <Show when={lecture.duration}>
                          <span class="text-xs text-muted">{formatDuration(lecture.duration)}</span>
                        </Show>
                        <Show when={lecture.audio_url}>
                          <button
                            type="button"
                            class="w-7 h-7 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center hover:bg-primary/30 transition-colors"
                            onClick={() => {
                              handlePlayRecent(lecture)
                            }}
                            aria-label={`Play ${lecture.title}`}
                          >
                            <svg
                              class="w-2.5 h-2.5 text-primary ml-0.5"
                              viewBox="0 0 14 16"
                              fill="currentColor"
                            >
                              <polygon points="0,0 14,8 0,16" />
                            </svg>
                          </button>
                        </Show>
                      </div>
                    </div>
                  </div>
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

      {/* ─── CTA Banner ─── */}
      <section class="px-6 md:px-12 lg:px-16 py-16">
        <div class="cta-banner max-w-7xl mx-auto">
          <div class="max-w-2xl">
            <h2 class="text-2xl md:text-3xl font-display text-foreground mb-3">
              Create Your Own Courses
            </h2>
            <p class="text-muted mb-6">
              Pick any subject, customize your professor, and generate complete lecture series with
              AI — all with natural-sounding audio.
            </p>
            <A href="/quickstart">
              <Button variant="primary" size="lg">
                Get Started Free
              </Button>
            </A>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home
