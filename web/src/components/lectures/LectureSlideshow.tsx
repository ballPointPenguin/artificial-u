import {
  type Component,
  createEffect,
  createMemo,
  createResource,
  createSignal,
  Show,
} from 'solid-js'
import { useAudioPlayer } from '../../utils/audio-player-context.jsx'

interface ImageSlot {
  index: number
  start: number
  end: number
  url: string | null
  status: string
  model?: string | null
}

interface ImagesTimeline {
  version: number
  lecture_id: number
  aspect_ratio?: string
  model?: string | null
  slots: ImageSlot[]
}

const fetchImagesTimeline = async (url: string): Promise<ImagesTimeline> => {
  const response = await fetch(url, { cache: 'no-store' })
  if (!response.ok) {
    throw new Error('Failed to fetch images timeline')
  }
  const body: unknown = await response.json()
  return body as ImagesTimeline
}

const findActiveSlotIndex = (slots: ImageSlot[], time: number): number => {
  if (!slots.length) return -1
  let lo = 0
  let hi = slots.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    const s = slots[mid]
    if (time < s.start) hi = mid - 1
    else if (time > s.end) lo = mid + 1
    else return mid
  }
  if (hi >= 0) return hi
  return 0
}

export interface LectureSlideshowProps {
  imagesTimelineUrl: string
  class?: string
}

export const LectureSlideshow: Component<LectureSlideshowProps> = (props) => {
  const player = useAudioPlayer()
  const [timeline] = createResource(() => props.imagesTimelineUrl, fetchImagesTimeline)

  const slots = createMemo(() => timeline()?.slots ?? [])
  const activeIdx = createMemo(() => findActiveSlotIndex(slots(), player.currentTime()))
  const activeSlot = createMemo(() => {
    const ss = slots()
    const idx = activeIdx()
    return idx >= 0 && idx < ss.length ? ss[idx] : null
  })
  const imageModel = createMemo(() => {
    const raw = activeSlot()?.model ?? timeline()?.model ?? null
    const trimmed = typeof raw === 'string' ? raw.trim() : null
    return trimmed || null
  })

  // Crossfade by tracking the last url we rendered.
  const [shownUrl, setShownUrl] = createSignal<string | null>(null)
  createEffect(() => {
    const url = activeSlot()?.url ?? null
    if (url && url !== shownUrl()) {
      setShownUrl(url)
    }
  })

  // Preload next image (best-effort).
  createEffect(() => {
    const ss = slots()
    const idx = activeIdx()
    const next = idx >= 0 && idx + 1 < ss.length ? ss[idx + 1] : null
    if (!next?.url) return
    const img = new Image()
    img.src = next.url
  })

  // Stage is 1:1. Cap max edge with min(100%, 50vh) so a fixed max-height (e.g. max-h-[40vh])
  // does not collapse the box to a wide strip; letterbox in <img> via object-contain.
  return (
    <div class="flex flex-col items-center">
      <div
        class={`relative mx-auto w-[min(100%,50vh)] max-w-full aspect-square shrink-0 overflow-hidden rounded-lg border border-border/60 bg-surface ${
          props.class ?? ''
        }`}
      >
        <Show
          when={!timeline.loading}
          fallback={<div class="h-full w-full animate-pulse bg-surface/60" />}
        >
          <Show
            when={!timeline.error && timeline() && activeSlot()}
            fallback={
              <div class="h-full w-full flex items-center justify-center text-muted text-sm">
                {timeline.error ? 'Failed to load lecture images.' : 'No lecture images.'}
              </div>
            }
          >
            <Show
              when={(activeSlot()?.status ?? 'pending') === 'done' && shownUrl()}
              fallback={
                <div class="h-full w-full flex items-center justify-center text-muted text-sm">
                  Generating images…
                </div>
              }
            >
              {(url) => (
                <img
                  src={url()}
                  alt="Lecture slide"
                  class="absolute inset-0 h-full w-full object-contain object-center transition-opacity duration-500 opacity-100"
                  loading="eager"
                  decoding="async"
                />
              )}
            </Show>
          </Show>
        </Show>
      </div>

      <Show when={imageModel()}>
        {(m) => (
          <p class="text-xs text-muted italic mt-2 text-center">Image generated with {m()}</p>
        )}
      </Show>
    </div>
  )
}
