import type { RouteSectionProps } from '@solidjs/router'
import { type Component, onCleanup, onMount } from 'solid-js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'
import { InstallPWAPrompt, PWAUpdatePrompt } from '../utils/pwa'
import { Footer } from './Footer'
import { NavBar } from './NavBar'
import { NowPlayingSheet } from './NowPlayingSheet.jsx'
import { PersistentAudioPlayer } from './PersistentAudioPlayer.jsx'
import { ThemeSwitcher } from './ThemeSwitcher'

// Don't hijack Space/arrow keys while the user is typing or interacting with form controls.
const isTypingTarget = (target: EventTarget | null): boolean => {
  if (!(target instanceof HTMLElement)) return false
  if (target.isContentEditable) return true
  const tag = target.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT'
}

const Layout: Component<RouteSectionProps> = (props) => {
  const player = useAudioPlayer()

  // Global keyboard shortcuts that apply whenever a track is loaded.
  onMount(() => {
    const handler = (e: KeyboardEvent) => {
      if (!player.currentTrack()) return
      if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey) return
      if (isTypingTarget(e.target)) return

      if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault()
        player.togglePlay()
      } else if (e.key === 'ArrowUp' && !player.isExpanded()) {
        e.preventDefault()
        player.expand()
      } else if (e.key === 'ArrowDown' && player.isExpanded()) {
        e.preventDefault()
        player.collapse()
      }
    }
    window.addEventListener('keydown', handler)
    onCleanup(() => {
      window.removeEventListener('keydown', handler)
    })
  })

  return (
    <div class="flex min-h-dvh flex-col bg-background text-foreground">
      <header class="shrink-0">
        <NavBar />
      </header>

      <div class="flex min-h-0 flex-1 flex-col">
        <div class="flex min-h-0 flex-1 flex-col lg:flex-row lg:items-start">
          <main class="min-w-0 flex-1">{props.children}</main>
          <NowPlayingSheet />
        </div>
      </div>

      <Footer />

      {/* Sticky bottom bar — audio player + theme switcher, in document flow */}
      <div class="sticky bottom-0 z-40">
        <PersistentAudioPlayer />
        <ThemeSwitcher />
      </div>

      {/* PWA Components — transient, keep fixed */}
      <PWAUpdatePrompt />
      <InstallPWAPrompt />
    </div>
  )
}

export default Layout
