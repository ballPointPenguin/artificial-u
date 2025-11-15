import { X } from 'lucide-solid'
import 'media-chrome'
import { type Component, createEffect, onCleanup, onMount, Show, untrack } from 'solid-js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'

export const PersistentAudioPlayer: Component = () => {
  const player = useAudioPlayer()
  let audioRef: HTMLAudioElement | undefined
  let controllerRef: HTMLElement | undefined
  let pendingRestoreTime: number | null = null

  const restoreFromPending = () => {
    if (!audioRef) return
    if (pendingRestoreTime == null) return
    if (!Number.isFinite(pendingRestoreTime) || pendingRestoreTime <= 0.25) {
      pendingRestoreTime = null
      return
    }
    if (Math.abs(audioRef.currentTime - pendingRestoreTime) > 0.35) {
      audioRef.currentTime = pendingRestoreTime
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

  // Sync audio element with context state
  onMount(() => {
    if (!audioRef) return

    // Capture ref in local variable to avoid closure issues
    const audio = audioRef

    // Set initial volume
    audio.volume = player.volume()

    // Listen to audio events and update context
    const handlePlay = () => {
      player.setIsPlaying(true)
    }
    const handlePause = () => {
      player.setIsPlaying(false)
      player.setCurrentTime(audio.currentTime || 0)
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
      restoreFromPending()
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
    if (!audioRef) return
    if (player.isPlaying()) {
      audioRef.play().catch((error: unknown) => {
        if (import.meta.env.DEV) {
          console.error('Failed to play audio:', error)
        }
      })
    } else {
      audioRef.pause()
    }
  })

  // Handle track changes
  createEffect(() => {
    const track = player.currentTrack()
    if (!audioRef || !track) return

    // Load new track
    audioRef.src = track.url
    const savedTime = untrack(() => player.currentTime())
    pendingRestoreTime = savedTime > 0.25 ? savedTime : null
    audioRef.load()
    if (audioRef.readyState >= 1) {
      queueMicrotask(() => {
        restoreFromPending()
      })
    }

    // If we're supposed to be playing, play
    const shouldAutoPlay = untrack(() => player.isPlaying())
    if (shouldAutoPlay) {
      audioRef.play().catch((error: unknown) => {
        if (import.meta.env.DEV) {
          console.error('Failed to play audio:', error)
        }
      })
    }
  })

  // Handle seek from context
  createEffect(() => {
    if (!audioRef) return
    const time = player.currentTime()
    if (Math.abs(audioRef.currentTime - time) > 0.5) {
      audioRef.currentTime = time
    }
  })

  // Handle volume from context
  createEffect(() => {
    if (!audioRef) return
    audioRef.volume = player.volume()
  })

  const handleClose = () => {
    player.clearTrack()
  }

  return (
    <Show when={player.currentTrack()}>
      {(track) => (
        <div class="fixed bottom-0 left-0 right-0 z-50 border-t border-parchment-800/50 bg-parchment-950/95 backdrop-blur-sm shadow-2xl">
          <button
            type="button"
            onClick={handleClose}
            class="absolute right-4 top-2 z-10 flex-shrink-0 rounded-full border border-parchment-800/50 bg-parchment-950/90 p-2 text-parchment-300 shadow-lg hover:text-parchment-100 hover:bg-parchment-800/70 transition-colors sm:right-6 sm:top-3"
            aria-label="Close player"
            title="Close player"
          >
            <X class="h-4 w-4" />
          </button>

          <div class="container mx-auto px-4 py-3">
            <div class="relative flex flex-col gap-4 pt-6 sm:flex-row sm:items-center sm:gap-6 sm:pt-0">
              {/* Track Info */}
              <div class="flex-1 min-w-0 space-y-1 pr-10">
                <h4 class="text-sm font-medium text-parchment-100 leading-tight whitespace-normal break-words sm:text-base">
                  {getShortName(track())}
                </h4>
                <Show when={track().subtitle}>
                  <p class="text-xs text-parchment-400 whitespace-normal break-words">
                    {track().subtitle}
                  </p>
                </Show>
              </div>

              {/* Media Chrome Player */}
              <div class="flex-[2] min-w-0 w-full">
                <media-controller
                  ref={controllerRef}
                  audio
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
                    ref={audioRef}
                    slot="media"
                    src={track().url}
                    preload="metadata"
                    crossOrigin="anonymous"
                  />
                  <media-control-bar class="flex flex-wrap items-center gap-x-2 gap-y-2 w-full">
                    <media-play-button class="text-parchment-100 hover:text-mystic-300 shrink-0" />
                    <media-seek-backward-button
                      seekoffset="10"
                      class="text-parchment-100 hover:text-mystic-300 shrink-0"
                    />
                    <media-seek-forward-button
                      seekoffset="10"
                      class="text-parchment-100 hover:text-mystic-300 shrink-0"
                    />
                    <media-mute-button class="text-parchment-100 hover:text-mystic-300 shrink-0" />
                    <media-volume-range class="w-full max-w-[180px] sm:w-24 basis-full sm:basis-auto" />
                    <media-time-range class="flex-1 min-w-[140px] basis-full sm:basis-auto mx-1" />
                    <media-time-display
                      showduration
                      class="text-xs text-parchment-300 min-w-[90px] text-center shrink-0"
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
