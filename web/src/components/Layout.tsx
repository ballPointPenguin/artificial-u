import type { RouteSectionProps } from '@solidjs/router'
import type { Component } from 'solid-js'
import { InstallPWAPrompt, PWAUpdatePrompt } from '../utils/pwa'
import { Footer } from './Footer'
import { NavBar } from './NavBar'
import { PersistentAudioPlayer } from './PersistentAudioPlayer.jsx'
import { ThemeSwitcher } from './ThemeSwitcher'

const Layout: Component<RouteSectionProps> = (props) => {
  return (
    <div class="flex flex-col min-h-dvh bg-background text-foreground">
      <header>
        <NavBar />
      </header>

      <main class="flex-grow">{props.children}</main>

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
