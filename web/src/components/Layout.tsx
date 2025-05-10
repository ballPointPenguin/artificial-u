import type { RouteSectionProps } from '@solidjs/router'
import type { Component } from 'solid-js'
import { NavBar } from './NavBar'
import { ThemeSwitcher } from './ThemeSwitcher'

const Layout: Component<RouteSectionProps> = (props) => {
  return (
    <div class="flex flex-col min-h-screen bg-background text-foreground">
      <header>
        <NavBar />
      </header>

      <main class="flex-grow">{props.children}</main>
      <ThemeSwitcher />
    </div>
  )
}

export default Layout
