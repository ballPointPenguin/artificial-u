import type { RouteSectionProps } from '@solidjs/router'
import type { Component } from 'solid-js'
import { NavBar } from './NavBar'
import { ThemeSwitcher } from './ThemeSwitcher'
import { PWAUpdatePrompt, InstallPWAPrompt } from '../utils/pwa'

const Layout: Component<RouteSectionProps> = (props) => {
  return (
    <div class="flex flex-col min-h-screen bg-background text-foreground">
      <header>
        <NavBar />
      </header>

      <main class="flex-grow">{props.children}</main>
      <ThemeSwitcher />

      {/* PWA Components */}
      <PWAUpdatePrompt />
      <InstallPWAPrompt />
    </div>
  )
}

export default Layout
