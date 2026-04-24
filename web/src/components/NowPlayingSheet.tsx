import { A } from '@solidjs/router'
import { ChevronDown, FastForward, ImageIcon, Pause, Play, Rewind, X } from 'lucide-solid'
import { type Component, createEffect, createSignal, onCleanup, onMount, Show } from 'solid-js'
import { Portal } from 'solid-js/web'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'
import { CaptionWindow } from './lectures/CaptionWindow.jsx'
import { LectureSlideshow } from './lectures/LectureSlideshow.jsx'

const formatTime = (seconds: number): string => {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
  const total = Math.floor(seconds)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const pad = (n: number) => String(n).padStart(2, '0')
  return h > 0 ? `${String(h)}:${pad(m)}:${pad(s)}` : `${String(m)}:${pad(s)}`
}

const NowPlayingSheetPanel: Component<{ view: 'docked' | 'overlay' }> = (props) => {
  const player = useAudioPlayer()
  const track = () => player.currentTrack()!

  const courseHref = (): string | null => {
    const t = player.currentTrack()
    if (!t?.courseId) return null
    if (t.lectureId) return `/courses/${String(t.courseId)}/lectures/${String(t.lectureId)}`
    if (t.topicId) return `/courses/${String(t.courseId)}/topics/${String(t.topicId)}`
    return `/courses/${String(t.courseId)}`
  }

  const contextLabel = (): string | null => {
    const t = player.currentTrack()
    if (!t) return null
    const parts: string[] = []
    if (t.courseCode) parts.push(t.courseCode)
    if (t.topicWeek != null && t.topicOrder != null) {
      parts.push(`Week ${String(t.topicWeek)} · Lecture ${String(t.topicOrder)}`)
    }
    return parts.length ? parts.join(' · ') : (t.subtitle ?? null)
  }

  const isDocked = () => props.view === 'docked'

  return (
    <section
      role={isDocked() ? 'complementary' : 'dialog'}
      aria-label="Now Playing"
      aria-modal={isDocked() ? false : 'true'}
      class={
        isDocked()
          ? 'flex min-h-0 w-[min(38rem,45vw)] max-w-full shrink-0 self-start sticky top-0 max-h-dvh flex-col border-l border-border bg-background text-foreground shadow-2xl'
          : 'fixed inset-0 z-50 flex min-h-0 flex-col bg-background text-foreground shadow-2xl'
      }
    >
      {/* Header */}
      <header class="flex shrink-0 items-start gap-3 px-4 py-3 sm:px-6 border-b border-border/60 bg-surface">
        <button
          type="button"
          onClick={() => {
            player.collapse()
          }}
          class="flex-shrink-0 rounded-full p-2 text-foreground/70 hover:text-foreground hover:bg-background/60 transition-colors"
          aria-label="Minimize player"
          title="Minimize (Esc)"
        >
          <ChevronDown class="h-5 w-5" />
        </button>

        <div class="flex-1 min-w-0 space-y-0.5">
          <Show when={contextLabel()}>
            {(label) => (
              <p class="text-xs uppercase tracking-wider text-mystic-400 truncate">{label()}</p>
            )}
          </Show>
          <h2 class="text-base sm:text-lg font-display text-foreground leading-tight truncate">
            {track().title}
          </h2>
          <Show when={track().subtitle && track().subtitle !== contextLabel()}>
            <p class="text-xs text-muted truncate">{track().subtitle}</p>
          </Show>
        </div>

        <Show when={courseHref()}>
          {(href) => (
            <A
              href={href()}
              onClick={() => {
                player.collapse()
              }}
              class="hidden sm:inline-flex flex-shrink-0 items-center gap-1 text-xs text-mystic-400 hover:text-mystic-300 underline underline-offset-2"
            >
              Open page
            </A>
          )}
        </Show>

        <button
          type="button"
          onClick={() => {
            player.clearTrack()
          }}
          class="flex-shrink-0 rounded-full p-2 text-foreground/70 hover:text-foreground hover:bg-background/60 transition-colors"
          aria-label="Close player"
          title="Close player"
        >
          <X class="h-5 w-5" />
        </button>
      </header>

      {/* Body: stage stays pinned, captions scroll within themselves */}
      <div class="flex-1 flex flex-col min-h-0 overflow-hidden px-4 sm:px-6 py-4 gap-4 bg-background">
        <Show
          when={track().imagesTimelineUrl}
          fallback={
            <div
              class="mx-auto w-[min(100%,50vh)] max-w-full aspect-square shrink-0 rounded-lg border border-dashed border-border/60
                     bg-surface flex items-center justify-center"
              aria-hidden="true"
            >
              <div class="flex flex-col items-center gap-2 text-muted">
                <ImageIcon class="h-10 w-10 opacity-60" />
                <p class="text-xs font-serif italic">Visuals coming soon</p>
              </div>
            </div>
          }
        >
          {(imagesTimelineUrl) => <LectureSlideshow imagesTimelineUrl={imagesTimelineUrl()} />}
        </Show>

        <Show
          when={track().timelineUrl}
          fallback={
            <div class="rounded-lg border border-border/60 bg-surface p-6 text-center">
              <p class="text-muted font-serif italic">
                No synchronized captions for this lecture yet.
              </p>
            </div>
          }
        >
          {(timelineUrl) => <CaptionWindow timelineUrl={timelineUrl()} class="min-h-0 flex-1" />}
        </Show>
      </div>

      {/* Transport footer — custom controls driving the shared audio via context. */}
      <footer class="shrink-0 border-t border-border/60 bg-surface px-4 sm:px-6 py-3 space-y-2">
        <div class="flex items-center gap-3">
          <span class="text-xs tabular-nums text-foreground/80 min-w-[3rem] text-right">
            {formatTime(player.currentTime())}
          </span>
          <input
            type="range"
            min="0"
            max={Math.max(player.duration(), 0.001)}
            step="0.1"
            value={player.currentTime()}
            onInput={(e) => {
              const v = Number.parseFloat(e.currentTarget.value)
              if (Number.isFinite(v)) player.seek(v)
            }}
            class="flex-1 h-1.5 rounded-full accent-mystic-400 bg-border/70 cursor-pointer"
            aria-label="Seek"
          />
          <span class="text-xs tabular-nums text-foreground/80 min-w-[3rem]">
            {formatTime(player.duration())}
          </span>
        </div>

        <div class="flex items-center justify-center gap-2 sm:gap-4">
          <button
            type="button"
            onClick={() => {
              player.seek(Math.max(0, player.currentTime() - 10))
            }}
            class="rounded-full p-2 text-foreground/80 hover:text-mystic-300 hover:bg-background/60 transition-colors"
            aria-label="Rewind 10 seconds"
            title="Rewind 10s"
          >
            <Rewind class="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={() => {
              player.togglePlay()
            }}
            class="rounded-full p-3 bg-mystic-500 text-background hover:bg-mystic-400 transition-colors shadow-md"
            aria-label={player.isPlaying() ? 'Pause' : 'Play'}
            title={player.isPlaying() ? 'Pause (Space)' : 'Play (Space)'}
          >
            <Show when={player.isPlaying()} fallback={<Play class="h-6 w-6" />}>
              <Pause class="h-6 w-6" />
            </Show>
          </button>
          <button
            type="button"
            onClick={() => {
              player.seek(
                Math.min(player.duration() || Number.POSITIVE_INFINITY, player.currentTime() + 10)
              )
            }}
            class="rounded-full p-2 text-foreground/80 hover:text-mystic-300 hover:bg-background/60 transition-colors"
            aria-label="Forward 10 seconds"
            title="Forward 10s"
          >
            <FastForward class="h-5 w-5" />
          </button>
        </div>
      </footer>
    </section>
  )
}

/**
 * NowPlayingSheet
 *
 * On narrow viewports the player is a full-screen sheet (portalled above the
 * app with a scrim). At `lg+` the player docks as a right-hand column in the
 * layout so the main content reflows to the remaining width instead of sitting
 * underneath a fixed overlay.
 */
export const NowPlayingSheet: Component = () => {
  const player = useAudioPlayer()

  const [isLg, setIsLg] = createSignal(
    typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches
  )

  onMount(() => {
    const mq = window.matchMedia('(min-width: 1024px)')
    const sync = () => {
      setIsLg(mq.matches)
    }
    sync()
    mq.addEventListener('change', sync)
    onCleanup(() => {
      mq.removeEventListener('change', sync)
    })
  })

  // Close on Escape
  createEffect(() => {
    if (!player.isExpanded()) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        player.collapse()
      }
    }
    window.addEventListener('keydown', handler)
    onCleanup(() => {
      window.removeEventListener('keydown', handler)
    })
  })

  // Lock body scroll while the mobile fullscreen sheet is open
  createEffect(() => {
    if (!player.isExpanded()) return
    // Only lock on narrow viewports where the sheet is full-screen
    const mq = window.matchMedia('(max-width: 1023px)')
    if (!mq.matches) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    onCleanup(() => {
      document.body.style.overflow = prev
    })
  })

  return (
    <Show when={player.isExpanded() && player.currentTrack()}>
      <Show
        when={isLg()}
        fallback={
          <Portal>
            <button
              type="button"
              aria-label="Close Now Playing"
              onClick={() => {
                player.collapse()
              }}
              class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            />
            <NowPlayingSheetPanel view="overlay" />
          </Portal>
        }
      >
        <NowPlayingSheetPanel view="docked" />
      </Show>
    </Show>
  )
}
