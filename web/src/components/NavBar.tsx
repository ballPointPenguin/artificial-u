import { A } from '@solidjs/router'
import { Show, createSignal } from 'solid-js'

export function NavBar() {
  const [isScrolled, setIsScrolled] = createSignal(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = createSignal(false)

  if (typeof window !== 'undefined') {
    window.addEventListener('scroll', () => {
      setIsScrolled(window.scrollY > 50)
    })
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen())
  }

  return (
    <nav
      class={`w-full z-50 transition-all duration-300 ${
        isScrolled() ? 'bg-arcanum-950/90 backdrop-blur-sm shadow-md' : 'bg-transparent'
      }`}
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          {/* Logo and site name */}
          <div>A|U</div>
          <div class="flex items-center">
            <A href="/" class="flex items-center">
              <div class="w-12 h-12 rounded-full border-2 border-parchment-300 overflow-hidden flex items-center justify-center bg-arcanum-900">
                <span class="text-parchment-200 font-display text-xl">A</span>
              </div>
              <div class="ml-3">
                <h1 class="text-parchment-200 font-display text-xl tracking-wider">
                  ARTIFICIAL UNIVERSITY
                </h1>
              </div>
            </A>
          </div>

          {/* Desktop Navigation */}
          <div class="hidden md:flex items-center space-x-8">
            <A
              href="/about"
              class="text-parchment-200 hover:text-parchment-100 tracking-wide font-serif uppercase text-shadow-golden text-sm"
            >
              About
            </A>
            <A
              href="/departments"
              class="text-parchment-200 hover:text-parchment-100 tracking-wide font-serif uppercase text-shadow-golden text-sm"
            >
              Departments
            </A>
            <A
              href="/professors"
              class="text-parchment-200 hover:text-parchment-100 tracking-wide font-serif uppercase text-shadow-golden text-sm"
            >
              Professors
            </A>
            <A
              href="/courses"
              class="text-parchment-200 hover:text-parchment-100 tracking-wide font-serif uppercase text-shadow-golden text-sm"
            >
              Courses
            </A>
          </div>

          {/* Mobile menu button */}
          <div class="md:hidden">
            <button
              type="button"
              onClick={toggleMobileMenu}
              class="text-parchment-200 hover:text-parchment-100"
            >
              <span class="sr-only">Open main menu</span>
              {isMobileMenuOpen() ? (
                <svg
                  class="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                <svg
                  class="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <Show when={isMobileMenuOpen()}>
        <div class="md:hidden bg-arcanum-950/95 backdrop-blur-sm">
          <div class="px-4 pt-2 pb-6 space-y-4">
            <A
              href="/about"
              class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif uppercase text-sm"
              onClick={toggleMobileMenu}
            >
              About
            </A>
            <A
              href="/departments"
              class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif uppercase text-sm"
              onClick={toggleMobileMenu}
            >
              Departments
            </A>
            <A
              href="/professors"
              class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif uppercase text-sm"
              onClick={toggleMobileMenu}
            >
              Professors
            </A>
            <A
              href="/courses"
              class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif uppercase text-sm"
              onClick={toggleMobileMenu}
            >
              Courses
            </A>
          </div>
        </div>
      </Show>
    </nav>
  )
}
