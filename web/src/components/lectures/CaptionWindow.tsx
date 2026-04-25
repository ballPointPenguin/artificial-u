import {
  type Component,
  createEffect,
  createMemo,
  createResource,
  For,
  onCleanup,
  onMount,
  Show,
} from 'solid-js'
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

interface Phrase {
  /** Real (non-whitespace) words in this phrase */
  words: TimelineEvent[]
  start: number
  end: number
  /** True for `[bracketed stage direction]` phrases; rendered with italics. */
  isBracket: boolean
}

const fetchTimeline = async (url: string): Promise<TimelineData> => {
  const response = await fetch(url, { cache: 'no-store' })
  if (!response.ok) {
    throw new Error('Failed to fetch timeline')
  }
  const body: unknown = await response.json()
  return body as TimelineData
}

// --- Chunking knobs (intentionally simple; tune to taste) ---------------------
// Phrase length targets in *real* (non-whitespace) words.
const TARGET_MIN_WORDS = 6
const TARGET_MAX_WORDS = 14
const HARD_MAX_WORDS = 18

// Punctuation hints. Trailing quotes / brackets are tolerated so "said.”" still
// counts as a sentence end.
const SENTENCE_END_RE = /[.!?…][")'\]]*$/
const CLAUSE_END_RE = /[,;:—–][")'\]]*$/

// ElevenLabs forced-alignment collapses `[bracketed stage directions]` into a
// single timeline "word" event. We treat any such event as its own phrase so
// it doesn't get mashed together with the following spoken line.
const BRACKET_RE = /^\s*\[[\s\S]*\]\s*$/

const flushBuf = (buf: TimelineEvent[], phrases: Phrase[]) => {
  if (buf.length === 0) return
  phrases.push({
    words: [...buf],
    start: buf[0].start,
    end: buf[buf.length - 1].end,
    isBracket: false,
  })
}

/**
 * Group forced-alignment word events into short, caption-sized phrases.
 *
 * Strategy is deliberately dumb and punctuation-driven:
 *   1. `[bracketed stage directions]` always get their own phrase, full stop.
 *   2. Break eagerly at . ! ? once we have at least TARGET_MIN words.
 *   3. Break at , ; : — once we're past TARGET_MAX words.
 *   4. Hard-cap at HARD_MAX words so a pause-less run of text still fits.
 *
 * Whitespace-only events from the timeline are discarded; we only care about
 * real words for chunking and display. This keeps the implementation tolerant
 * of ElevenLabs' habit of emitting a separate "word" event for every space.
 */
const chunkIntoPhrases = (events: TimelineEvent[]): Phrase[] => {
  const realWords = events.filter(
    (e) => e.type === 'word' && typeof e.content === 'string' && e.content.trim() !== ''
  )
  const phrases: Phrase[] = []
  let buf: TimelineEvent[] = []

  for (let i = 0; i < realWords.length; i++) {
    const w = realWords[i]
    const content = w.content ?? ''
    const isLast = i === realWords.length - 1

    // Bracket stage direction — flush any pending buffer, then give it its
    // own phrase. Happens even if the current buffer is small: the direction
    // marks a clear visual/audible break anyway.
    if (BRACKET_RE.test(content)) {
      flushBuf(buf, phrases)
      buf = []
      phrases.push({
        words: [w],
        start: w.start,
        end: w.end,
        isBracket: true,
      })
      continue
    }

    buf.push(w)

    const endsSentence = SENTENCE_END_RE.test(content)
    const endsClause = CLAUSE_END_RE.test(content)
    const len = buf.length

    const shouldBreak =
      isLast ||
      (endsSentence && len >= TARGET_MIN_WORDS) ||
      (endsClause && len >= TARGET_MAX_WORDS) ||
      len >= HARD_MAX_WORDS

    if (shouldBreak) {
      flushBuf(buf, phrases)
      buf = []
    }
  }

  return phrases
}

/** Binary search for the phrase whose time range contains `time`. */
const findActivePhraseIndex = (phrases: Phrase[], time: number): number => {
  if (!phrases.length) return -1
  let lo = 0
  let hi = phrases.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    const p = phrases[mid]
    if (time < p.start) {
      hi = mid - 1
    } else if (time > p.end) {
      lo = mid + 1
    } else {
      return mid
    }
  }
  // Fall back to the nearest phrase so the caption stays populated in any gap
  // between phrases. Clamp to 0 for times before the very first phrase.
  if (hi >= 0) return hi
  return 0
}

export interface CaptionWindowProps {
  timelineUrl: string
  class?: string
}

/**
 * CaptionWindow — karaoke-style caption panel.
 *
 * Shows one phrase at a time with active-word highlighting and soft
 * "already said / not yet said" shading. No scrolling, no full-text view.
 * The whole phrase lives in a fixed-size card, so navigating between phrases
 * feels like a clean cut rather than a crawl through a wall of text.
 */
export const CaptionWindow: Component<CaptionWindowProps> = (props) => {
  const player = useAudioPlayer()
  const [timeline] = createResource(() => props.timelineUrl, fetchTimeline)

  const phrases = createMemo<Phrase[]>(() => {
    const data = timeline()
    if (!data) return []
    return chunkIntoPhrases(data.events)
  })

  const activePhraseIdx = createMemo(() => findActivePhraseIndex(phrases(), player.currentTime()))

  const activePhrase = createMemo<Phrase | null>(() => {
    const ps = phrases()
    const idx = activePhraseIdx()
    return idx >= 0 && idx < ps.length ? ps[idx] : null
  })

  /** Index (within the active phrase) of the word currently being spoken, or -1 in gaps. */
  const activeWordInPhrase = createMemo(() => {
    const phrase = activePhrase()
    if (!phrase) return -1
    const t = player.currentTime()
    for (let i = 0; i < phrase.words.length; i++) {
      const w = phrase.words[i]
      if (t >= w.start && t <= w.end) return i
    }
    return -1
  })

  /** Index of the last word whose spoken interval has started (for past/future coloring). */
  const spokenCursor = createMemo(() => {
    const phrase = activePhrase()
    if (!phrase) return -1
    const t = player.currentTime()
    let last = -1
    for (let i = 0; i < phrase.words.length; i++) {
      if (t >= phrase.words[i].start) last = i
      else break
    }
    return last
  })

  const handleWordClick = (start: number) => {
    player.seek(start)
    if (!player.isPlaying()) {
      player.resume()
    }
  }

  // --- Auto-fit font size -----------------------------------------------------
  // Rather than bucket by token count, we measure-and-shrink: binary-search the
  // largest font size at which the phrase fits the card's content area on both
  // axes. Re-runs whenever the phrase changes or the card resizes (e.g. the
  // desktop Now Playing sheet narrows). Handles any content — technical terms,
  // German compounds, long bracket directions — by construction, no bucket
  // maintenance required.
  let cardRef: HTMLDivElement | undefined
  let pRef: HTMLParagraphElement | undefined

  const MIN_FONT_PX = 14
  const MAX_FONT_PX = 44

  let fitScheduled = false
  const scheduleFit = () => {
    if (fitScheduled) return
    fitScheduled = true
    requestAnimationFrame(() => {
      fitScheduled = false
      fitText()
    })
  }

  const fitText = () => {
    const p = pRef
    const card = cardRef
    if (!p || !card) return

    const style = getComputedStyle(card)
    const padX = Number.parseFloat(style.paddingLeft) + Number.parseFloat(style.paddingRight)
    const padY = Number.parseFloat(style.paddingTop) + Number.parseFloat(style.paddingBottom)
    const availW = card.clientWidth - padX
    const availH = card.clientHeight - padY
    if (availW <= 0 || availH <= 0) return

    let lo = MIN_FONT_PX
    let hi = MAX_FONT_PX
    let best = MIN_FONT_PX

    while (lo <= hi) {
      const mid = (lo + hi) >> 1
      p.style.fontSize = `${String(mid)}px`
      const fits = p.scrollHeight <= availH && p.scrollWidth <= availW
      if (fits) {
        best = mid
        lo = mid + 1
      } else {
        hi = mid - 1
      }
    }

    p.style.fontSize = `${String(best)}px`
  }

  // Re-fit when the phrase content changes. `activePhrase()` is the dependency
  // that matters; deferring to the next frame lets Solid finish updating the
  // DOM before we measure.
  createEffect(() => {
    activePhrase()
    scheduleFit()
  })

  // Re-fit when the card itself resizes (desktop sidebar, mobile rotation, etc).
  onMount(() => {
    if (!cardRef) return
    const ro = new ResizeObserver(() => {
      scheduleFit()
    })
    ro.observe(cardRef)
    onCleanup(() => {
      ro.disconnect()
    })
  })

  return (
    <div
      ref={(el) => {
        cardRef = el
      }}
      class={`relative min-h-0 w-full max-h-full rounded-lg bg-surface border border-border/60 flex items-center justify-center p-6 sm:p-8 overflow-hidden ${
        props.class ?? ''
      }`}
    >
      <Show
        when={!timeline.loading}
        fallback={<span class="text-muted animate-pulse">Loading captions...</span>}
      >
        <Show
          when={!timeline.error && timeline()}
          fallback={<span class="text-red-400">Failed to load captions.</span>}
        >
          <Show
            when={activePhrase()}
            fallback={<span class="text-muted italic font-serif">…</span>}
          >
            {(phrase) => (
              <p
                ref={(el) => {
                  pRef = el
                }}
                class="leading-relaxed font-serif text-center max-w-prose break-words"
                classList={{
                  // Stage directions read as descriptive meta-text, not speech.
                  // Italicizing them (and dimming slightly) matches screenplay
                  // convention and helps the viewer parse "this is a cue, not
                  // a line" at a glance.
                  'italic text-foreground/70': phrase().isBracket,
                }}
              >
                <For each={phrase().words}>
                  {(word, index) => {
                    const isActive = () => activeWordInPhrase() === index()
                    const isPast = () => !isActive() && spokenCursor() >= index()
                    return (
                      <>
                        <span
                          onClick={() => {
                            handleWordClick(word.start)
                          }}
                          class="cursor-pointer transition-colors duration-150"
                          classList={{
                            'text-mystic-300': isActive(),
                            'text-foreground': isPast(),
                            'text-foreground/40': !isActive() && !isPast(),
                            'hover:text-mystic-400': !isActive(),
                          }}
                        >
                          {word.content}
                        </span>
                        {index() < phrase().words.length - 1 ? ' ' : ''}
                      </>
                    )
                  }}
                </For>
              </p>
            )}
          </Show>
        </Show>
      </Show>
    </div>
  )
}
