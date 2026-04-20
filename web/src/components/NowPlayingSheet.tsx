import { A } from '@solidjs/router'
import {
  ChevronDown,
  ImageIcon,
  Pause,
  Play,
  Rewind,
  FastForward,
  X,
} from 'lucide-solid'
import { type Component, createEffect, onCleanup, Show } from 'solid-js'
import { Portal } from 'solid-js/web'
import { CaptionWindow } from './lectures/CaptionWindow.jsx'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'

const formatTime = (seconds: number): string => {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
  const total = Math.floor(seconds)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const pad = (n: number) => String(n).padStart(2, '0')
  return h > 0 ? `${String(h)}:${pad(m)}:${pad(s)}` : `${String(m)}:${pad(s)}`
}

/**
 * NowPlayingSheet
 *
 * The immersive "Now Playing" view. On mobile it's a full-screen sheet that slides
 * up from the bottom. On desktop (lg+) it docks as a right-hand side-drawer so the
 * user can keep browsing on the left.
 *
 * Content is driven entirely by `useAudioPlayer()` — this component lives in the
 * layout so it survives route changes. A future slides/image feed is expected to
 * fill the "stage" area above the captions.
 */
export const NowPlayingSheet: Component = () => {
  const player = useAudioPlayer()

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

  return (
    <Show when={player.isExpanded() && player.currentTrack()}>
      {(track) => (
        <Portal>
          {/* Backdrop — only visible on mobile full-screen mode */}
          <button
            type="button"
            aria-label="Close Now Playing"
            onClick={() => { player.collapse(); }}
            class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:bg-transparent lg:backdrop-blur-none lg:pointer-events-none"
          />

          <section
            role="dialog"
            aria-modal="true"
            aria-label="Now Playing"
            class="fixed inset-0 z-50 flex flex-col bg-background text-foreground shadow-2xl
                   lg:inset-y-0 lg:right-0 lg:left-auto lg:w-[min(38rem,45vw)]
                   lg:border-l lg:border-border"
          >
            {/* Header */}
            <header class="flex items-start gap-3 px-4 py-3 sm:px-6 border-b border-border/60 bg-surface">
              <button
                type="button"
                onClick={() => { player.collapse(); }}
                class="flex-shrink-0 rounded-full p-2 text-foreground/70 hover:text-foreground hover:bg-background/60 transition-colors"
                aria-label="Minimize player"
                title="Minimize (Esc)"
              >
                <ChevronDown class="h-5 w-5" />
              </button>

              <div class="flex-1 min-w-0 space-y-0.5">
                <Show when={contextLabel()}>
                  {(label) => (
                    <p class="text-xs uppercase tracking-wider text-mystic-400 truncate">
                      {label()}
                    </p>
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
                    onClick={() => { player.collapse(); }}
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
            <div class="flex-1 flex flex-col min-h-0 px-4 sm:px-6 py-4 gap-4 bg-background">
              {/* Stage area — fixed aspect, never scrolls out of view.
                  `max-h-[40vh]` prevents the stage from dominating tall-narrow
                  viewports and starving the caption area. */}
              <div
                class="aspect-video w-full flex-shrink-0 max-h-[40vh] rounded-lg border border-dashed border-border/60
                       bg-surface flex items-center justify-center"
                aria-hidden="true"
              >
                <div class="flex flex-col items-center gap-2 text-muted">
                  <ImageIcon class="h-10 w-10 opacity-60" />
                  <p class="text-xs font-serif italic">Visuals coming soon</p>
                </div>
              </div>

              {/* Captions — fill remaining height, scroll internally.
                  `min-h-[12rem]` guarantees readable caption height even when
                  the sheet gets vertically squeezed. */}
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
                {(timelineUrl) => (
                  <CaptionWindow timelineUrl={timelineUrl()} class="flex-1 min-h-[12rem]" />
                )}
              </Show>
            </div>

            {/* Transport footer — custom controls driving the shared audio via context.
                The real <audio> element lives in PersistentAudioPlayer; these buttons
                just update AudioPlayerContext state, which that player reacts to. */}
            <footer class="border-t border-border/60 bg-surface px-4 sm:px-6 py-3 space-y-2">
              {/* Progress slider */}
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

              {/* Transport buttons */}
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
                      Math.min(
                        player.duration() || Number.POSITIVE_INFINITY,
                        player.currentTime() + 10
                      )
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
        </Portal>
      )}
    </Show>
  )
}
