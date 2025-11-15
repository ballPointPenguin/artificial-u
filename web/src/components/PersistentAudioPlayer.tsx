import { X } from 'lucide-solid'
import 'media-chrome'
import { type Component, Show, createEffect, onCleanup, onMount } from 'solid-js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'

export const PersistentAudioPlayer: Component = () => {
  const player = useAudioPlayer()
  let audioRef: HTMLAudioElement | undefined
  let controllerRef: HTMLElement | undefined

  // Sync audio element with context state
  onMount(() => {
    if (!audioRef) return

    // Set initial volume
    audioRef.volume = player.volume()

    // Listen to audio events and update context
    const handlePlay = () => player.setIsPlaying(true)
    const handlePause = () => player.setIsPlaying(false)
    const handleTimeUpdate = () => player.setCurrentTime(audioRef?.currentTime || 0)
    const handleDurationChange = () => player.setDuration(audioRef?.duration || 0)
    const handleVolumeChange = () => player.setVolume(audioRef?.volume || 0.7)

    audioRef.addEventListener('play', handlePlay)
    audioRef.addEventListener('pause', handlePause)
    audioRef.addEventListener('timeupdate', handleTimeUpdate)
    audioRef.addEventListener('durationchange', handleDurationChange)
    audioRef.addEventListener('volumechange', handleVolumeChange)

    onCleanup(() => {
      audioRef?.removeEventListener('play', handlePlay)
      audioRef?.removeEventListener('pause', handlePause)
      audioRef?.removeEventListener('timeupdate', handleTimeUpdate)
      audioRef?.removeEventListener('durationchange', handleDurationChange)
      audioRef?.removeEventListener('volumechange', handleVolumeChange)
    })
  })

  // Handle play/pause from context
  createEffect(() => {
    if (!audioRef) return
    if (player.isPlaying()) {
      void audioRef.play()
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
    audioRef.load()

    // If we're supposed to be playing, play
    if (player.isPlaying()) {
      void audioRef.play()
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
    player.stop()
    player.playTrack({
      url: '',
      title: '',
    })
    // This will cause currentTrack to be null, hiding the player
  }

  return (
    <Show when={player.currentTrack()}>
      {(track) => (
        <div class="fixed bottom-0 left-0 right-0 z-50 border-t border-parchment-800/50 bg-parchment-950/95 backdrop-blur-sm shadow-2xl">
          <div class="container mx-auto px-4 py-3">
            <div class="flex items-center gap-4">
              {/* Track Info */}
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-medium text-parchment-100 truncate">{track().title}</h4>
                <Show when={track().subtitle}>
                  <p class="text-xs text-parchment-400 truncate">{track().subtitle}</p>
                </Show>
              </div>

              {/* Media Chrome Player */}
              <div class="flex-[2] min-w-0">
                <media-controller
                  ref={controllerRef}
                  audio
                  class="w-full"
                  style={{
                    '--media-control-height': '32px',
                    '--media-control-background': 'transparent',
                    '--media-control-hover-background': 'rgba(199, 210, 254, 0.1)',
                    '--media-range-track-height': '4px',
                    '--media-range-thumb-height': '12px',
                    '--media-range-thumb-width': '12px',
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
                  <media-control-bar class="flex items-center gap-2 w-full">
                    <media-play-button class="text-parchment-100 hover:text-mystic-300" />
                    <media-seek-backward-button seekoffset="10" class="text-parchment-100 hover:text-mystic-300" />
                    <media-seek-forward-button seekoffset="10" class="text-parchment-100 hover:text-mystic-300" />
                    <media-time-range class="flex-1 mx-2" />
                    <media-time-display
                      showduration
                      class="text-xs text-parchment-300 min-w-[100px] text-center"
                    />
                    <media-mute-button class="text-parchment-100 hover:text-mystic-300" />
                    <media-volume-range class="w-20" />
                    <media-playback-rate-button class="text-parchment-100 hover:text-mystic-300 text-xs" />
                  </media-control-bar>
                </media-controller>
              </div>

              {/* Close Button */}
              <button
                onClick={handleClose}
                class="flex-shrink-0 p-2 text-parchment-400 hover:text-parchment-200 transition-colors"
                aria-label="Close player"
                title="Close player"
              >
                <X class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </Show>
  )
}
