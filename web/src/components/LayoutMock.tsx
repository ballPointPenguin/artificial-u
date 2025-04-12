import type { Component, JSX } from 'solid-js'

// A simplified version of Layout component for testing, without router dependencies
const LayoutMock: Component<{ children?: JSX.Element }> = (props) => {
  return (
    <div class="flex flex-col min-h-screen bg-gray-900 text-white">
      <nav class="bg-gray-800 p-4">
        <ul class="flex space-x-4">
          <li>
            <a href="/" class="text-blue-400 hover:text-blue-600">
              Home
            </a>
          </li>
          <li>
            <a href="/about" class="text-blue-400 hover:text-blue-600">
              About
            </a>
          </li>
        </ul>
      </nav>

      <main class="flex-grow p-4">{props.children}</main>
    </div>
  )
}

export default LayoutMock
