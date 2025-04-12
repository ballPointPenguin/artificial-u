import type { Component } from 'solid-js'
import { A, type RouteSectionProps } from '@solidjs/router'

const Layout: Component<RouteSectionProps> = (props) => {
  return (
    <div class="flex flex-col min-h-screen bg-gray-900 text-white">
      <nav class="bg-gray-800 p-4">
        <ul class="flex space-x-4">
          <li>
            <A href="/" class="text-blue-400 hover:text-blue-600" end>
              Home
            </A>
          </li>
          <li>
            <A href="/about" class="text-blue-400 hover:text-blue-600">
              About
            </A>
          </li>
        </ul>
      </nav>

      <main class="flex-grow p-4">{props.children}</main>
    </div>
  )
}

export default Layout
