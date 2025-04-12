import { DropdownMenu } from '@kobalte/core'
import { A, type RouteSectionProps } from '@solidjs/router'
import { type Component, Show, createSignal } from 'solid-js'

const Layout: Component<RouteSectionProps> = (props) => {
  const [isMenuOpen, setIsMenuOpen] = createSignal(false)

  return (
    <div class="flex flex-col min-h-screen bg-gray-50 text-gray-900 font-sans">
      <header class="bg-white shadow-md sticky top-0 z-10">
        <div class="container mx-auto px-4">
          <div class="flex items-center justify-between h-16">
            {/* Logo and site name */}
            <div class="flex-shrink-0 flex items-center">
              <A href="/" class="flex items-center">
                <span class="text-xl font-bold text-blue-600">
                  Artificial University
                </span>
              </A>
            </div>

            {/* Desktop Navigation */}
            <nav class="hidden md:ml-6 md:flex md:space-x-6">
              <A
                href="/"
                class="text-gray-700 hover:text-blue-600 hover:bg-gray-50 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                activeClass="text-blue-700 font-semibold"
                end
              >
                Dashboard
              </A>
              <A
                href="/departments"
                class="text-gray-700 hover:text-blue-600 hover:bg-gray-50 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                activeClass="text-blue-700 font-semibold"
              >
                Departments
              </A>
              <A
                href="/about"
                class="text-gray-700 hover:text-blue-600 hover:bg-gray-50 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                activeClass="text-blue-700 font-semibold"
              >
                About
              </A>
            </nav>

            {/* User dropdown using Kobalte */}
            <div class="hidden md:flex items-center">
              <DropdownMenu.Root>
                <DropdownMenu.Trigger class="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-50 hover:text-blue-600 focus:outline-none">
                  <span>Account</span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="ml-1 h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </DropdownMenu.Trigger>
                <DropdownMenu.Portal>
                  <DropdownMenu.Content class="bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none mt-2 py-1 min-w-[200px] z-50">
                    <DropdownMenu.Item class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Profile
                    </DropdownMenu.Item>
                    <DropdownMenu.Item class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Settings
                    </DropdownMenu.Item>
                    <DropdownMenu.Separator class="my-1 h-px bg-gray-200" />
                    <DropdownMenu.Item class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      Sign out
                    </DropdownMenu.Item>
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu.Root>
            </div>

            {/* Mobile menu button */}
            <div class="md:hidden flex items-center">
              <button
                type="button"
                class="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                onClick={() => setIsMenuOpen(!isMenuOpen())}
                aria-expanded={isMenuOpen()}
              >
                <span class="sr-only">
                  {isMenuOpen() ? 'Close menu' : 'Open menu'}
                </span>
                <svg
                  class="h-6 w-6"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <Show
                    when={!isMenuOpen()}
                    fallback={
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M6 18L18 6M6 6l12 12"
                      />
                    }
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  </Show>
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <Show when={isMenuOpen()}>
          <div class="md:hidden bg-white border-t border-gray-200">
            <div class="px-2 pt-2 pb-3 space-y-1">
              <A
                href="/"
                class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                activeClass="bg-blue-50 text-blue-700"
                end
              >
                Dashboard
              </A>
              <A
                href="/departments"
                class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                activeClass="bg-blue-50 text-blue-700"
              >
                Departments
              </A>
              <A
                href="/about"
                class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                activeClass="bg-blue-50 text-blue-700"
              >
                About
              </A>
              <div class="border-t border-gray-200 pt-4 pb-3">
                <div class="px-3 space-y-1">
                  <a
                    href="/profile"
                    class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                  >
                    Profile
                  </a>
                  <a
                    href="/settings"
                    class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                  >
                    Settings
                  </a>
                  <a
                    href="/signout"
                    class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                  >
                    Sign out
                  </a>
                </div>
              </div>
            </div>
          </div>
        </Show>
      </header>

      <main class="flex-grow container mx-auto px-4 py-6">
        {props.children}
      </main>

      <footer class="bg-white shadow-inner py-6">
        <div class="container mx-auto px-4">
          <div class="flex flex-col md:flex-row justify-between items-center">
            <p class="text-gray-500">
              Artificial University &copy; {new Date().getFullYear()}
            </p>
            <div class="flex space-x-4 mt-4 md:mt-0">
              <a
                href="/terms"
                class="text-gray-500 hover:text-blue-600 transition-colors"
              >
                Terms
              </a>
              <a
                href="/privacy"
                class="text-gray-500 hover:text-blue-600 transition-colors"
              >
                Privacy
              </a>
              <a
                href="/contact"
                class="text-gray-500 hover:text-blue-600 transition-colors"
              >
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
