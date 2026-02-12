import type { RouteSectionProps } from '@solidjs/router'
import type { Component } from 'solid-js'
import { useAudioPlayer } from '../utils/audio-player-context.jsx'
import { InstallPWAPrompt, PWAUpdatePrompt } from '../utils/pwa'
import { Footer } from './Footer'
import { NavBar } from './NavBar'
import { PersistentAudioPlayer } from './PersistentAudioPlayer.jsx'
import { ThemeSwitcher } from './ThemeSwitcher'

const Layout: Component<RouteSectionProps> = (props) => {
  const audioPlayer = useAudioPlayer()

  return (
    <div class="flex flex-col min-h-dvh bg-background text-foreground">
      <header>
        <NavBar />
      </header>

      <main class="flex-grow">
        {props.children}
      </main>

      <div classList={{ 'pb-52 sm:pb-44 md:pb-36': !!audioPlayer.currentTrack() }}>
        <Footer />
      </div>
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
