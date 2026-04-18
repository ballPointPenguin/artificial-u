import { type Component, createEffect, createResource, createSignal, For, onCleanup, Show } from 'solid-js'
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
  return response.json()
}

export const AnimatedCaptions: Component<{ timelineUrl: string }> = (props) => {
  const player = useAudioPlayer()
  const [timeline] = createResource(() => props.timelineUrl, fetchTimeline)

  // Create a ref for the container to handle auto-scrolling
  let containerRef: HTMLDivElement | undefined

  // Track active word index for efficient updates
  const [activeIndex, setActiveIndex] = createSignal<number>(-1)

  // Sync active word with audio time using requestAnimationFrame for performance
  createEffect(() => {
    const data = timeline()
    if (!data || !data.events.length) return

    const words = data.events.filter(e => e.type === 'word')

    let animationFrameId: number

    const updateActiveWord = () => {
      // Only run if playing to save CPU
      if (player.isPlaying()) {
        const time = player.currentTime()

        // Find the current active word
        // Optimization: check around the current active index first
        let newIndex = -1
        const currentIdx = activeIndex()

        if (currentIdx >= 0 && currentIdx < words.length) {
          const currentWord = words[currentIdx]
          if (time >= currentWord.start && time <= currentWord.end) {
            newIndex = currentIdx
          } else if (currentIdx + 1 < words.length && time >= words[currentIdx + 1].start && time <= words[currentIdx + 1].end) {
            newIndex = currentIdx + 1
          } else {
            // Fallback to binary search or linear search
            newIndex = words.findIndex(w => time >= w.start && time <= w.end)
          }
        } else {
          newIndex = words.findIndex(w => time >= w.start && time <= w.end)
        }

        if (newIndex !== activeIndex()) {
          setActiveIndex(newIndex)

          // Auto-scroll to active word
          if (newIndex !== -1 && containerRef) {
            const activeElement = containerRef.querySelector(`[data-index="${newIndex}"]`)
            if (activeElement) {
              activeElement.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
              })
            }
          }
        }
      }

      animationFrameId = requestAnimationFrame(updateActiveWord)
    }

    animationFrameId = requestAnimationFrame(updateActiveWord)

    onCleanup(() => {
      cancelAnimationFrame(animationFrameId)
    })
  })

  // Handle manual seek when clicking a word
  const handleWordClick = (start: number) => {
    player.seek(start)
    if (!player.isPlaying()) {
      player.resume()
    }
  }

  return (
    <div class="w-full bg-parchment-900/30 rounded-lg p-6 border border-parchment-800/50">
      <h3 class="text-lg font-display text-parchment-200 mb-4 flex items-center gap-2">
        <span class="inline-block w-2 h-2 rounded-full bg-mystic-500 animate-pulse" />
        Live Captions
      </h3>

      <Show
        when={!timeline.loading}
        fallback={<div class="text-parchment-400 animate-pulse">Loading captions...</div>}
      >
        <Show
          when={!timeline.error && timeline()}
          fallback={<div class="text-red-400">Failed to load captions.</div>}
        >
          <div
            ref={containerRef}
            class="max-h-[400px] overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-parchment-700 scrollbar-track-transparent"
          >
            <div class="text-xl leading-loose font-serif text-parchment-400">
              <For each={timeline()?.events.filter(e => e.type === 'word')}>
                {(word, index) => {
                  const isActive = () => activeIndex() === index()
                  const isPast = () => activeIndex() > index()

                  return (
                    <span
                      data-index={index()}
                      onClick={() => handleWordClick(word.start)}
                      class="inline-block mx-1 cursor-pointer transition-all duration-200"
                      classList={{
                        'text-mystic-300 font-medium scale-110 drop-shadow-md': isActive(),
                        'text-parchment-200': isPast() && !isActive(),
                        'hover:text-mystic-400': !isActive()
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
