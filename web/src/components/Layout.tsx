import type { RouteSectionProps } from '@solidjs/router'
import type { Component } from 'solid-js'
import { InstallPWAPrompt, PWAUpdatePrompt } from '../utils/pwa'
import { NavBar } from './NavBar'
import { PersistentAudioPlayer } from './PersistentAudioPlayer.jsx'
import { ThemeSwitcher } from './ThemeSwitcher'

const Layout: Component<RouteSectionProps> = (props) => {
  return (
    <div class="flex flex-col min-h-screen bg-background text-foreground">
      <header>
        <NavBar />
      </header>

      <main class="flex-grow pb-24">{props.children}</main>
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
