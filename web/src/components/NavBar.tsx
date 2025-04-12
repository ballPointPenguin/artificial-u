import { Button } from '@kobalte/core/button'
import { A } from '@solidjs/router'
import { Show, createSignal } from 'solid-js'

export function NavBar() {
  const [isScrolled, setIsScrolled] = createSignal(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = createSignal(false)
  const [isAcademicsOpen, setIsAcademicsOpen] = createSignal(false)

  if (typeof window !== 'undefined') {
    window.addEventListener('scroll', () => {
      setIsScrolled(window.scrollY > 50)
    })
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen())
    setIsAcademicsOpen(false)
  }

  const toggleAcademicsMenu = () => {
    setIsAcademicsOpen(!isAcademicsOpen())
  }

  return (
    <nav
      class={`w-full z-50 transition-all duration-300 ${
        isScrolled()
          ? 'bg-arcanum-950/90 backdrop-blur-sm shadow-md'
          : 'bg-transparent'
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
            <div class="relative">
              <button
                type="button"
                onClick={toggleAcademicsMenu}
                class="flex items-center text-parchment-200 hover:text-parchment-100 tracking-wide font-serif uppercase text-shadow-golden text-sm"
              >
                Academics
                <svg
                  class="w-4 h-4 ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d={isAcademicsOpen() ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'}
                  />
                </svg>
              </button>
              <Show when={isAcademicsOpen()}>
                <div class="absolute left-0 mt-2 w-48 bg-arcanum-900 shadow-lg rounded-md py-2 z-10">
                  <A
                    href="/academics/departments"
                    class="block px-4 py-2 text-parchment-200 hover:bg-arcanum-800 tracking-wide font-serif text-sm"
                    onClick={() => setIsAcademicsOpen(false)}
                  >
                    Departments
                  </A>
                  <A
                    href="#"
                    class="block px-4 py-2 text-parchment-200 hover:bg-arcanum-800 tracking-wide font-serif text-sm"
                    onClick={() => setIsAcademicsOpen(false)}
                  >
                    Programs
                  </A>
                  <A
                    href="#"
                    class="block px-4 py-2 text-parchment-200 hover:bg-arcanum-800 tracking-wide font-serif text-sm"
                    onClick={() => setIsAcademicsOpen(false)}
                  >
                    Courses
                  </A>
                </div>
              </Show>
            </div>
            <A
              href="/admissions"
              class="text-parchment-200 hover:text-parchment-100 tracking-wide font-serif uppercase text-shadow-golden text-sm"
            >
              Admissions
            </A>
            <A
              href="/library"
              class="text-parchment-200 hover:text-parchment-100 tracking-wide font-serif uppercase text-shadow-golden text-sm"
            >
              Library
            </A>
            <Button class="ml-4 px-6 py-2 rounded border border-parchment-400 text-parchment-100 font-display tracking-wider hover:bg-parchment-800/20 transition-colors duration-300 text-sm">
              Apply
            </Button>
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
            <div>
              <button
                type="button"
                onClick={toggleAcademicsMenu}
                class="flex items-center w-full text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif uppercase text-sm"
              >
                Academics
                <svg
                  class="w-4 h-4 ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d={isAcademicsOpen() ? 'M19 9l-7 7-7-7' : 'M9 5l7 7-7 7'}
                  />
                </svg>
              </button>
              <Show when={isAcademicsOpen()}>
                <div class="pl-4 mt-1 space-y-1 border-l border-arcanum-700">
                  <A
                    href="/academics/departments"
                    class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif text-sm"
                    onClick={toggleMobileMenu}
                  >
                    Departments
                  </A>
                  <A
                    href="#"
                    class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif text-sm"
                    onClick={toggleMobileMenu}
                  >
                    Programs
                  </A>
                  <A
                    href="#"
                    class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif text-sm"
                    onClick={toggleMobileMenu}
                  >
                    Courses
                  </A>
                </div>
              </Show>
            </div>
            <A
              href="/admissions"
              class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif uppercase text-sm"
              onClick={toggleMobileMenu}
            >
              Admissions
            </A>
            <A
              href="/library"
              class="block text-parchment-200 hover:text-parchment-100 py-2 tracking-wide font-serif uppercase text-sm"
              onClick={toggleMobileMenu}
            >
              Library
            </A>
            <A
              href="/apply"
              class="block text-center mt-4 px-6 py-2 rounded border border-parchment-400 text-parchment-100 font-display tracking-wider hover:bg-parchment-800/20 transition-colors duration-300 text-sm"
              onClick={toggleMobileMenu}
            >
              Apply
            </A>
          </div>
        </div>
      </Show>
    </nav>
  )
}
