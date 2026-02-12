import { createSignal, For, Show } from 'solid-js'
import type { RecentLecture } from '../api/types.js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'

interface FeaturedLectureCarouselProps {
  lectures: RecentLecture[]
  label?: string
}

function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins)}:${String(secs).padStart(2, '0')}`
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

export function FeaturedLectureCarousel(props: FeaturedLectureCarouselProps) {
  const [currentIndex, setCurrentIndex] = createSignal(0)
  const audioPlayer = useAudioPlayer()

  const goTo = (index: number) => {
    const len = props.lectures.length
    if (len === 0) return
    setCurrentIndex(((index % len) + len) % len)
  }

  const prev = () => {
    goTo(currentIndex() - 1)
  }
  const next = () => {
    goTo(currentIndex() + 1)
  }

  const currentLecture = () => props.lectures[currentIndex()]

  const handlePlay = (lecture: RecentLecture) => {
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
    <div class="bg-surface border border-border rounded-lg p-6 lg:max-w-md lg:ml-auto relative">
      {/* Label */}
      <div class="section-label mb-4">{props.label ?? 'Featured Lectures'}</div>

      {/* Current slide */}
      <Show when={currentLecture()}>
        {(lecture) => (
          <div class="min-h-[180px]">
            {/* Play button + title row */}
            <div class="flex items-start gap-3 mb-1">
              <button
                type="button"
                class="mt-1 w-9 h-9 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center flex-shrink-0 hover:bg-primary/30 transition-colors"
                onClick={() => {
                  handlePlay(lecture())
                }}
                aria-label="Play lecture"
              >
                <svg
                  class="w-3.5 h-3.5 text-primary ml-0.5"
                  viewBox="0 0 14 16"
                  fill="currentColor"
                >
                  <polygon points="0,0 14,8 0,16" />
                </svg>
              </button>
              <div class="flex-1 min-w-0">
                <h3 class="font-display text-lg text-foreground leading-snug">{lecture().title}</h3>
              </div>
            </div>

            {/* Meta: week, course, duration */}
            <p class="text-xs font-sans text-muted mt-2 mb-4">
              <Show when={lecture().topic_week}>
                <span>Week {lecture().topic_week}</span>
                <span class="mx-1">&middot;</span>
              </Show>
              <Show when={lecture().course_code}>
                <span>{lecture().course_code}</span>
                <Show when={lecture().course_title}>
                  <span>: {lecture().course_title}</span>
                </Show>
                <span class="mx-1">&middot;</span>
              </Show>
              <Show when={lecture().duration}>
                <span class="text-primary font-medium">{formatDuration(lecture().duration)}</span>
              </Show>
            </p>

            {/* Professor row */}
            <Show when={lecture().professor_name}>
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-secondary/20 border border-secondary/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
                  <Show
                    when={lecture().professor_image_url}
                    fallback={
                      <span class="font-sans text-xs font-semibold text-secondary">
                        {getInitials(lecture().professor_name!)}
                      </span>
                    }
                  >
                    <img
                      src={lecture().professor_image_url!}
                      alt={lecture().professor_name!}
                      class="w-10 h-10 rounded-full object-cover"
                    />
                  </Show>
                </div>
                <div class="min-w-0">
                  <div class="text-sm font-medium text-foreground truncate">
                    {lecture().professor_name}
                  </div>
                  <div class="text-xs text-muted truncate">
                    <Show when={lecture().department_name}>
                      <span>{lecture().department_name}</span>
                    </Show>
                    <Show when={lecture().professor_accent}>
                      <span class="mx-1">&middot;</span>
                      <span>{lecture().professor_accent} accent</span>
                    </Show>
                  </div>
                </div>
              </div>
            </Show>
          </div>
        )}
      </Show>

      {/* Carousel navigation */}
      <Show when={props.lectures.length > 1}>
        <div class="flex items-center justify-between mt-4">
          <button
            type="button"
            onClick={prev}
            class="w-8 h-8 rounded-full border border-border bg-surface hover:border-primary/40 hover:text-primary flex items-center justify-center text-muted transition-colors"
            aria-label="Previous lecture"
          >
            &#8249;
          </button>

          <div class="flex gap-2">
            <For each={props.lectures}>
              {(_, i) => (
                <button
                  type="button"
                  onClick={() => {
                    goTo(i())
                  }}
                  class={`w-2 h-2 rounded-full transition-all ${
                    i() === currentIndex() ? 'bg-primary scale-125' : 'bg-border hover:bg-muted'
                  }`}
                  aria-label={`Go to lecture ${String(i() + 1)}`}
                />
              )}
            </For>
          </div>

          <button
            type="button"
            onClick={next}
            class="w-8 h-8 rounded-full border border-border bg-surface hover:border-primary/40 hover:text-primary flex items-center justify-center text-muted transition-colors"
            aria-label="Next lecture"
          >
            &#8250;
          </button>
        </div>
      </Show>
    </div>
  )
}
