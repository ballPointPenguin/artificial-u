import { ChevronUp, X } from 'lucide-solid'
import 'media-chrome'
import { type Component, createEffect, createSignal, onCleanup, Show, untrack } from 'solid-js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'

export const PersistentAudioPlayer: Component = () => {
  const player = useAudioPlayer()

  // Signal-backed ref so effects react when the <audio> element mounts/unmounts.
  // (It lives inside <Show when={currentTrack}>, so it is NOT available at first
  // render on a fresh session — a plain `let audioRef` misses the initial mount
  // and leaves timeupdate/play/pause listeners permanently unattached.)
  const [audioEl, setAudioEl] = createSignal<HTMLAudioElement | null>(null)
  let pendingRestoreTime: number | null = null
  let previousTrackKey: string | null = null

  const trackKey = (t: ReturnType<typeof player.currentTrack>): string | null => {
    if (!t) return null
    // Some deployments may serve lecture audio from a stable URL (e.g. a proxy endpoint),
    // so URL alone is not a reliable "new track" identifier.
    return `${String(t.lectureId ?? t.topicId ?? '')}::${t.url}`
  }

  const restoreFromPending = (audio: HTMLAudioElement) => {
    if (pendingRestoreTime == null) return
    if (!Number.isFinite(pendingRestoreTime) || pendingRestoreTime <= 0.25) {
      pendingRestoreTime = null
      return
    }
    if (Math.abs(audio.currentTime - pendingRestoreTime) > 0.35) {
      audio.currentTime = pendingRestoreTime
    }
    pendingRestoreTime = null
  }

  // Generate short display name for track (e.g., "CAN350_1_2")
  const getShortName = (track: ReturnType<typeof player.currentTrack>) => {
    if (!track) return ''
    const { courseCode, topicWeek, topicOrder } = track
    if (courseCode && topicWeek != null && topicOrder != null) {
      return `${courseCode}_${String(topicWeek)}_${String(topicOrder)}`
    }
    return track.title
  }

  // Attach listeners whenever the <audio> element mounts. Detach on unmount.
  createEffect(() => {
    const audio = audioEl()
    if (!audio) return

    audio.volume = untrack(() => player.volume())

    const handlePlay = () => {
      player.setIsPlaying(true)
    }
    const handlePause = () => {
      player.setIsPlaying(false)
      player.setCurrentTime(audio.currentTime || 0)
      player.saveCurrentTime()
    }
    const handleTimeUpdate = () => {
      player.setCurrentTime(audio.currentTime || 0)
    }
    const handleDurationChange = () => {
      player.setDuration(audio.duration || 0)
    }
    const handleVolumeChange = () => {
      player.setVolume(audio.volume || 0.7)
    }
    const handleLoadedMetadata = () => {
      restoreFromPending(audio)
    }
    const handleError = () => {
      if (import.meta.env.DEV) {
        console.error('Audio playback error')
      }
    }

    audio.addEventListener('play', handlePlay)
    audio.addEventListener('pause', handlePause)
    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('durationchange', handleDurationChange)
    audio.addEventListener('volumechange', handleVolumeChange)
    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('error', handleError)

    onCleanup(() => {
      audio.removeEventListener('play', handlePlay)
      audio.removeEventListener('pause', handlePause)
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('durationchange', handleDurationChange)
      audio.removeEventListener('volumechange', handleVolumeChange)
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('error', handleError)
    })
  })

  // Handle play/pause from context
  createEffect(() => {
    const audio = audioEl()
    if (!audio) return
    if (player.isPlaying()) {
      audio.play().catch((error: unknown) => {
        if (import.meta.env.DEV) {
          console.error('Failed to play audio:', error)
        }
        player.setIsPlaying(false)
      })
    } else {
      audio.pause()
    }
  })

  // Handle track changes
  createEffect(() => {
    const audio = audioEl()
    const track = player.currentTrack()
    if (!audio || !track) {
      previousTrackKey = null
      return
    }

    const nextKey = trackKey(track)
    const isNewTrack = previousTrackKey !== nextKey
    previousTrackKey = nextKey

    audio.src = track.url

    if (isNewTrack) {
      pendingRestoreTime = null
      player.setCurrentTime(0)
      audio.currentTime = 0
    } else {
      const savedTime = untrack(() => player.currentTime())
      pendingRestoreTime = savedTime > 0.25 ? savedTime : null
    }

    audio.load()
    if (audio.readyState >= 1) {
      queueMicrotask(() => {
        restoreFromPending(audio)
        if (isNewTrack) {
          audio.currentTime = 0
        }
      })
    }

    const shouldAutoPlay = untrack(() => player.isPlaying())
    if (shouldAutoPlay) {
      audio.play().catch((error: unknown) => {
        if (import.meta.env.DEV) {
          console.error('Failed to play audio:', error)
        }
      })
    }
  })

  // Handle explicit seek requests from the UI. We subscribe to `seekRequest`
  // (not `currentTime`) so ongoing `timeupdate` events can't race a seek into
  // oblivion: if the user clicks a caption word, we want exactly that seek to
  // land, regardless of whether a queued `timeupdate` then writes the old
  // position back into `currentTime`.
  createEffect(() => {
    const req = player.seekRequest()
    const audio = audioEl()
    if (!req || !audio) return
    if (Math.abs(audio.currentTime - req.time) > 0.05) {
      audio.currentTime = req.time
    }
  })

  // Handle volume from context
  createEffect(() => {
    const audio = audioEl()
    if (!audio) return
    audio.volume = player.volume()
  })

  const handleClose = () => {
    player.clearTrack()
  }

  return (
    <Show when={player.currentTrack()}>
      {(track) => (
        <div
          class="w-full border-t border-parchment-800/50 bg-parchment-950/95 backdrop-blur-sm shadow-2xl"
          classList={{
            // Hide the mini-bar entirely while the Now Playing sheet is open.
            // The <audio> element is still present in the DOM, so playback continues.
            hidden: player.isExpanded(),
          }}
          aria-hidden={player.isExpanded() ? 'true' : 'false'}
        >
          {/* Action cluster (expand + close) */}
          <div class="absolute right-2 top-2 z-10 flex items-center gap-1 sm:right-4 sm:top-3">
            <button
              type="button"
              onClick={() => {
                player.expand()
              }}
              class="rounded-full border border-parchment-800/50 bg-parchment-950/90 p-2 text-parchment-300 shadow-lg hover:text-parchment-100 hover:bg-parchment-800/70 transition-colors"
              aria-label="Expand player"
              title="Expand player"
            >
              <ChevronUp class="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={handleClose}
              class="rounded-full border border-parchment-800/50 bg-parchment-950/90 p-2 text-parchment-300 shadow-lg hover:text-parchment-100 hover:bg-parchment-800/70 transition-colors"
              aria-label="Close player"
              title="Close player"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <div class="container mx-auto px-4 py-3">
            <div class="relative flex flex-col gap-4 pt-6 sm:flex-row sm:items-center sm:gap-6 sm:pt-0">
              {/* Track Info — clicking expands the Now Playing sheet */}
              <button
                type="button"
                onClick={() => {
                  player.expand()
                }}
                class="flex-1 min-w-0 space-y-1 pr-20 text-left cursor-pointer hover:opacity-90 transition-opacity"
                aria-label="Open Now Playing"
              >
                <h4 class="text-sm font-medium text-parchment-100 leading-tight whitespace-normal break-words sm:text-base">
                  {getShortName(track())}
                </h4>
                <Show when={track().subtitle}>
                  <p class="text-xs text-parchment-400 whitespace-normal break-words">
                    {track().subtitle}
                  </p>
                </Show>
              </button>

              {/* Media Chrome Player */}
              <div class="flex-[2] min-w-0 w-full">
                <media-controller
                  ref={() => {}}
                  audio
                  nohotkeys
                  class="persistent-audio-controller w-full overflow-visible sm:max-w-[calc(100%-3.5rem)]"
                  style={{
                    '--media-control-background': 'transparent',
                    '--media-control-hover-background': 'rgba(199, 210, 254, 0.1)',
                    '--media-primary-color': '#c7d2fe',
                    '--media-secondary-color': '#a5b4fc',
                    '--media-text-color': '#f5f5dc',
                  }}
                >
                  <audio
                    ref={setAudioEl}
                    slot="media"
                    src={track().url}
                    preload="metadata"
                    crossOrigin="anonymous"
                  />
                  <media-control-bar class="flex flex-wrap items-center gap-x-1 sm:gap-x-2 gap-y-2 w-full">
                    <media-play-button class="text-parchment-100 hover:text-mystic-300 shrink-0" />
                    <media-seek-backward-button
                      seekoffset="10"
                      class="text-parchment-100 hover:text-mystic-300 shrink-0"
                    />
                    <media-seek-forward-button
                      seekoffset="10"
                      class="text-parchment-100 hover:text-mystic-300 shrink-0"
                    />
                    <media-mute-button class="text-parchment-100 hover:text-mystic-300 shrink-0 hidden sm:block" />
                    <media-volume-range class="w-24 shrink-0 hidden sm:block" />
                    <media-time-range class="flex-1 min-w-[100px] basis-full sm:basis-auto order-last sm:order-none mx-1" />
                    <media-time-display
                      showduration
                      class="text-xs text-parchment-300 min-w-[80px] text-center shrink-0"
                    />
                    <media-playback-rate-button class="text-parchment-100 hover:text-mystic-300 text-xs shrink-0" />
                  </media-control-bar>
                </media-controller>
              </div>
            </div>
          </div>
        </div>
      )}
    </Show>
  )
}
