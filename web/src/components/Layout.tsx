import { A, type RouteSectionProps } from '@solidjs/router'
import type { Component } from 'solid-js'

const Layout: Component<RouteSectionProps> = (props) => {
  return (
    <div class="flex flex-col min-h-screen bg-gray-100 text-gray-900">
      <nav class="bg-white shadow-md p-4">
        <div class="container mx-auto">
          <ul class="flex space-x-6">
            <li>
              <A
                href="/"
                class="text-blue-600 hover:text-blue-800 font-medium"
                activeClass="font-bold text-blue-800 border-b-2 border-blue-800"
                end
              >
                Home
              </A>
            </li>
            <li>
              <A
                href="/departments"
                class="text-blue-600 hover:text-blue-800 font-medium"
                activeClass="font-bold text-blue-800 border-b-2 border-blue-800"
              >
                Departments
              </A>
            </li>
            <li>
              <A
                href="/about"
                class="text-blue-600 hover:text-blue-800 font-medium"
                activeClass="font-bold text-blue-800 border-b-2 border-blue-800"
              >
                About
              </A>
            </li>
          </ul>
        </div>
      </nav>

      <main class="flex-grow py-6">{props.children}</main>

      <footer class="bg-white shadow-inner p-4 mt-8">
        <div class="container mx-auto text-center text-gray-500">
          <p>Artificial University &copy; {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  )
}

export default Layout
