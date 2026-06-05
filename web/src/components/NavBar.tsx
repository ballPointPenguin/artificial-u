import { A } from '@solidjs/router'
import { createSignal, Show } from 'solid-js'
import { useAuth } from '../auth/AuthProvider'
import { useTranslations } from '../i18n'
import { LocaleSwitcher } from './LocaleSwitcher'

export function NavBar() {
  const [isScrolled, setIsScrolled] = createSignal(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = createSignal(false)
  const auth = useAuth()
  const t = useTranslations()

  if (typeof window !== 'undefined') {
    window.addEventListener('scroll', () => {
      setIsScrolled(window.scrollY > 50)
    })
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen())
  }

  // Shared link classes
  const linkClass =
    'text-muted hover:text-primary font-sans text-xs font-medium uppercase tracking-widest transition-colors duration-200'
  const mobileLinkClass =
    'block text-foreground/80 hover:text-primary py-2 font-sans text-sm uppercase tracking-wider transition-colors'

  return (
    <nav
      class={`w-full z-50 transition-all duration-300 border-b border-border/40 ${
        isScrolled() ? 'bg-background/95 backdrop-blur-sm shadow-sm' : 'bg-transparent'
      }`}
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-3">
          {/* Brand */}
          <A href="/" class="flex items-center gap-3 no-underline">
            <div class="w-9 h-9 rounded-full border-2 border-secondary flex items-center justify-center">
              <span class="font-display text-sm text-secondary font-bold">A</span>
            </div>
            <span class="font-display text-sm tracking-[0.12em] uppercase text-foreground">
              {t().site.name}
            </span>
          </A>

          {/* Desktop Navigation */}
          <div class="hidden md:flex items-center gap-7">
            <A href="/search" class={linkClass}>
              {t().nav.search}
            </A>
            <A href="/courses" class={linkClass}>
              {t().nav.courses}
            </A>
            <A href="/academics" class={linkClass}>
              {t().nav.departments}
            </A>
            <Show when={auth.isAuthenticated()}>
              <A href="/profile" class={linkClass}>
                {t().nav.profile}
              </A>
            </Show>
            <Show when={auth.isAdmin()}>
              <A href="/admin" class={linkClass}>
                {t().nav.admin}
              </A>
            </Show>

            {/* Auth CTA */}
            <Show
              when={!auth.isAuthenticated()}
              fallback={
                <button type="button" onClick={() => void auth.logout()} class={linkClass}>
                  {t().nav.logout}
                </button>
              }
            >
              <A
                href="/login"
                class="ml-1 px-4 py-1.5 border border-primary rounded text-primary font-sans text-xs font-medium uppercase tracking-widest hover:bg-primary hover:text-on-primary transition-all duration-200"
              >
                {t().nav.login}
              </A>
            </Show>

            <div class="ml-2 pl-3 border-l border-border/30">
              <LocaleSwitcher />
            </div>
          </div>

          {/* Mobile menu button */}
          <div class="md:hidden">
            <button
              type="button"
              onClick={toggleMobileMenu}
              class="text-foreground/70 hover:text-foreground p-1"
            >
              <span class="sr-only">{t().nav.openMenu}</span>
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
        <div class="md:hidden bg-background/95 backdrop-blur-sm border-t border-border/30">
          <div class="px-4 pt-2 pb-6 space-y-1">
            <A href="/search" class={mobileLinkClass} onClick={toggleMobileMenu}>
              {t().nav.search}
            </A>
            <A href="/courses" class={mobileLinkClass} onClick={toggleMobileMenu}>
              {t().nav.courses}
            </A>
            <A href="/academics" class={mobileLinkClass} onClick={toggleMobileMenu}>
              {t().nav.departments}
            </A>
            <Show when={auth.isAuthenticated()}>
              <A href="/profile" class={mobileLinkClass} onClick={toggleMobileMenu}>
                {t().nav.profile}
              </A>
            </Show>
            <Show when={auth.isAdmin()}>
              <A href="/admin" class={mobileLinkClass} onClick={toggleMobileMenu}>
                {t().nav.admin}
              </A>
            </Show>
            <Show when={!auth.isAuthenticated()}>
              <A href="/login" class={mobileLinkClass} onClick={toggleMobileMenu}>
                {t().nav.login}
              </A>
            </Show>
            <Show when={auth.isAuthenticated()}>
              <button
                class={mobileLinkClass}
                type="button"
                onClick={() => {
                  toggleMobileMenu()
                  void auth.logout()
                }}
              >
                {t().nav.logout}
              </button>
            </Show>
            <div class="pt-4 border-t border-border/30">
              <LocaleSwitcher />
            </div>
          </div>
        </div>
      </Show>
    </nav>
  )
}
