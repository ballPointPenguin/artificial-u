import { type Component, createEffect, createMemo, createResource, For, Show } from 'solid-js'
import { useAudioPlayer } from '../../utils/audio-player-context.jsx'

interface TimelineEvent {
  type: string
  content?: string
  url?: string
  start: number
  end: number
}

interface TimelineData {
  events: TimelineEvent[]
}

const fetchTimeline = async (url: string): Promise<TimelineData> => {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error('Failed to fetch timeline')
  }
  const body: unknown = await response.json()
  return body as TimelineData
}

// Binary search for the word whose [start, end) interval contains `time`.
// Returns -1 if no interval contains time.
const findActiveWordIndex = (words: TimelineEvent[], time: number): number => {
  if (!words.length) return -1
  let lo = 0
  let hi = words.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    const w = words[mid]
    if (time < w.start) {
      hi = mid - 1
    } else if (time > w.end) {
      lo = mid + 1
    } else {
      return mid
    }
  }
  // Fall back to "most recent word that has started" so the caret stays sensible in inter-word gaps
  if (hi >= 0 && time >= words[hi].start) return hi
  return -1
}

export interface AnimatedCaptionsProps {
  timelineUrl: string
  /** Visual size: 'md' matches the old inline display; 'lg' is for the Now Playing sheet */
  size?: 'md' | 'lg'
  /** Max height for the scrollable area; omit to let the parent size it */
  maxHeight?: string
  /** Show the "Live Captions" header row (default true) */
  showHeader?: boolean
  class?: string
}

export const AnimatedCaptions: Component<AnimatedCaptionsProps> = (props) => {
  const player = useAudioPlayer()
  const [timeline] = createResource(() => props.timelineUrl, fetchTimeline)

  let containerRef: HTMLDivElement | undefined

  // Memoized list of word-level events (stable identity unless the timeline resource changes)
  const words = createMemo<TimelineEvent[]>(() => {
    const data = timeline()
    if (!data) return []
    return data.events.filter((e) => e.type === 'word')
  })

  // Reactive active-word index. Updates on every currentTime tick AND on seek/scrub,
  // whether or not the player is currently playing.
  const activeIndex = createMemo(() => findActiveWordIndex(words(), player.currentTime()))

  // Auto-scroll only when the active word is out of view. `block: 'nearest'`
  // (vs. 'center') keeps the browser from re-centering on every word tick,
  // which was causing the visible jitter between words.
  createEffect(() => {
    const idx = activeIndex()
    if (idx < 0 || !containerRef) return
    const el = containerRef.querySelector<HTMLElement>(`[data-index="${String(idx)}"]`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })

  const handleWordClick = (start: number) => {
    player.seek(start)
    if (!player.isPlaying()) {
      player.resume()
    }
  }

  const textSizeClass = () => (props.size === 'lg' ? 'text-xl md:text-2xl' : 'text-xl')
  const leadingClass = () => (props.size === 'lg' ? 'leading-relaxed' : 'leading-loose')
  // When `maxHeight` is provided, use it; otherwise size='md' falls back to a
  // fixed cap and size='lg' expects the parent to provide the height (via flex),
  // in which case the scroll area fills available space.
  const containerMaxHeight = () => props.maxHeight ?? (props.size === 'lg' ? '' : 'max-h-[400px]')

  return (
    <div
      class={`w-full bg-parchment-900/30 rounded-lg p-4 sm:p-6 border border-parchment-800/50 flex flex-col ${
        props.class ?? ''
      }`}
    >
      <Show when={props.showHeader ?? true}>
        <h3 class="text-lg font-display text-parchment-200 mb-4 flex-shrink-0 flex items-center gap-2">
          <span class="inline-block w-2 h-2 rounded-full bg-mystic-500 animate-pulse" />
          Live Captions
        </h3>
      </Show>

      <Show
        when={!timeline.loading}
        fallback={<div class="text-parchment-400 animate-pulse">Loading captions...</div>}
      >
        <Show
          when={!timeline.error && timeline()}
          fallback={<div class="text-red-400">Failed to load captions.</div>}
        >
          <div
            ref={(el) => {
              containerRef = el
            }}
            class={`flex-1 min-h-0 overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-parchment-700 scrollbar-track-transparent ${containerMaxHeight()}`}
          >
            <div class={`${textSizeClass()} ${leadingClass()} font-serif text-parchment-400`}>
              <For each={words()}>
                {(word, index) => {
                  const isActive = () => activeIndex() === index()
                  const isPast = () => activeIndex() > index()

                  return (
                    <span
                      data-index={index()}
                      onClick={() => {
                        handleWordClick(word.start)
                      }}
                      class="inline-block mx-1 cursor-pointer transition-colors duration-150 [scroll-margin-top:4rem] [scroll-margin-bottom:6rem]"
                      classList={{
                        'text-mystic-300': isActive(),
                        'text-parchment-200': isPast() && !isActive(),
                        'hover:text-mystic-400': !isActive(),
                      }}
                    >
                      {word.content}
                    </span>
                  )
                }}
              </For>
            </div>
          </div>
        </Show>
      </Show>
    </div>
  )
}
