import type { Accessor, ParentComponent } from 'solid-js'
import { createContext, createEffect, createSignal, onCleanup, useContext } from 'solid-js'

export interface AudioTrack {
  url: string
  title: string
  subtitle?: string // e.g., "Week 1 - Introduction"
  timelineUrl?: string // URL to the JSON timeline for forced alignment captions
  courseId?: number
  lectureId?: number
  topicId?: number
  courseCode?: string
  topicWeek?: number
  topicOrder?: number
}

interface AudioPlayerState {
  currentTrack: AudioTrack | null
  isPlaying: boolean
  currentTime: number
  duration: number
  volume: number
}

interface AudioPlayerContextValue {
  // State accessors
  currentTrack: Accessor<AudioTrack | null>
  isPlaying: Accessor<boolean>
  currentTime: Accessor<number>
  duration: Accessor<number>
  volume: Accessor<number>

  // Actions
  playTrack: (track: AudioTrack) => void
  clearTrack: () => void
  pause: () => void
  resume: () => void
  stop: () => void
  seek: (time: number) => void
  setVolume: (volume: number) => void
  setCurrentTime: (time: number) => void
  setDuration: (duration: number) => void
  setIsPlaying: (playing: boolean) => void
  saveCurrentTime: () => void
}

const AudioPlayerContext = createContext<AudioPlayerContextValue>()

const STORAGE_KEY = 'artificial-u-audio-player-state'

// Load initial state from localStorage
const loadState = (): Partial<AudioPlayerState> => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored) as Partial<AudioPlayerState>
    }
  } catch (error) {
    console.error('Failed to load audio player state:', error)
  }
  return {}
}

// Save state to localStorage
const saveState = (state: Partial<AudioPlayerState>) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('Failed to save audio player state:', error)
  }
}

export const AudioPlayerProvider: ParentComponent = (props) => {
  const initialState = loadState()

  const [currentTrack, setCurrentTrack] = createSignal<AudioTrack | null>(
    initialState.currentTrack || null
  )
  const [isPlaying, setIsPlaying] = createSignal(false) // Don't auto-play on load
  const [currentTime, setCurrentTime] = createSignal(initialState.currentTime || 0)
  const [duration, setDuration] = createSignal(initialState.duration || 0)
  const [volume, setVolume] = createSignal(initialState.volume ?? 0.7)

  // Persist track, duration, and volume changes to localStorage (infrequent updates)
  createEffect(() => {
    const state: Partial<AudioPlayerState> = {
      currentTrack: currentTrack(),
      duration: duration(),
      volume: volume(),
      // Don't save currentTime here - it's saved periodically during playback
      currentTime: 0,
    }
    saveState(state)
  })

  // Save currentTime to localStorage (called on pause/stop and periodically during playback)
  const saveCurrentTime = () => {
    const state: Partial<AudioPlayerState> = {
      currentTrack: currentTrack(),
      currentTime: currentTime(),
      duration: duration(),
      volume: volume(),
    }
    saveState(state)
  }

  // Periodically save progress during playback (every 3 seconds)
  createEffect(() => {
    if (isPlaying()) {
      const intervalId = setInterval(() => {
        saveCurrentTime()
      }, 3000) // Save every 3 seconds

      onCleanup(() => {
        clearInterval(intervalId)
      })
    }
  })

  const playTrack = (track: AudioTrack) => {
    setCurrentTrack(track)
    setIsPlaying(true)
    setCurrentTime(0)
  }

  const clearTrack = () => {
    setCurrentTrack(null)
    setIsPlaying(false)
    setCurrentTime(0)
    setDuration(0)
  }

  const pause = () => {
    setIsPlaying(false)
    saveCurrentTime() // Save position when pausing
  }

  const resume = () => {
    setIsPlaying(true)
  }

  const stop = () => {
    setIsPlaying(false)
    setCurrentTime(0)
    saveCurrentTime() // Save position when stopping
  }

  const seek = (time: number) => {
    setCurrentTime(time)
  }

  const value: AudioPlayerContextValue = {
    currentTrack,
    isPlaying,
    currentTime,
    duration,
    volume,
    playTrack,
    clearTrack,
    pause,
    resume,
    stop,
    seek,
    setVolume,
    setCurrentTime,
    setDuration,
    setIsPlaying,
    saveCurrentTime,
  }

  return <AudioPlayerContext.Provider value={value}>{props.children}</AudioPlayerContext.Provider>
}

export const useAudioPlayer = () => {
  const context = useContext(AudioPlayerContext)
  if (!context) {
    throw new Error('useAudioPlayer must be used within an AudioPlayerProvider')
  }
  return context
}
