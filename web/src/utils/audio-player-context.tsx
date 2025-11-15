import type { Accessor, ParentComponent } from 'solid-js'
import { createContext, createEffect, createSignal, useContext } from 'solid-js'

export interface AudioTrack {
  url: string
  title: string
  subtitle?: string // e.g., "Week 1 - Introduction"
  courseId?: number
  lectureId?: number
  topicId?: number
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
  pause: () => void
  resume: () => void
  stop: () => void
  seek: (time: number) => void
  setVolume: (volume: number) => void
  setCurrentTime: (time: number) => void
  setDuration: (duration: number) => void
  setIsPlaying: (playing: boolean) => void
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

  // Persist state changes to localStorage
  createEffect(() => {
    const state: Partial<AudioPlayerState> = {
      currentTrack: currentTrack(),
      currentTime: currentTime(),
      duration: duration(),
      volume: volume(),
    }
    saveState(state)
  })

  const playTrack = (track: AudioTrack) => {
    setCurrentTrack(track)
    setIsPlaying(true)
    setCurrentTime(0)
  }

  const pause = () => {
    setIsPlaying(false)
  }

  const resume = () => {
    setIsPlaying(true)
  }

  const stop = () => {
    setIsPlaying(false)
    setCurrentTime(0)
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
    pause,
    resume,
    stop,
    seek,
    setVolume,
    setCurrentTime,
    setDuration,
    setIsPlaying,
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
