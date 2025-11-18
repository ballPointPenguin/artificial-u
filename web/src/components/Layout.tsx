import type { RouteSectionProps } from '@solidjs/router'
import type { Component } from 'solid-js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'
import { InstallPWAPrompt, PWAUpdatePrompt } from '../utils/pwa'
import { NavBar } from './NavBar'
import { PersistentAudioPlayer } from './PersistentAudioPlayer.jsx'
import { ThemeSwitcher } from './ThemeSwitcher'

const Layout: Component<RouteSectionProps> = (props) => {
  const audioPlayer = useAudioPlayer()

  return (
    <div class="flex flex-col min-h-screen bg-background text-foreground">
      <header>
        <NavBar />
      </header>

      <main classList={{ 'flex-grow': true, 'pb-36 sm:pb-28 md:pb-24': !!audioPlayer.currentTrack() }}>
        {props.children}
      </main>
      <ThemeSwitcher />

      {/* PWA Components */}
      <PWAUpdatePrompt />
      <InstallPWAPrompt />

      {/* Persistent Audio Player */}
      <PersistentAudioPlayer />
    </div>
  )
}

export default Layout
