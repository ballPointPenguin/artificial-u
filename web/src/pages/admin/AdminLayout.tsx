import type { RouteSectionProps } from '@solidjs/router'
import { A, useLocation } from '@solidjs/router'
import { createMemo, createSignal, For, Show } from 'solid-js'

type AdminNavItem = {
  href: string
  label: string
}

const NAV_ITEMS: AdminNavItem[] = [
  { href: '/admin/users', label: 'Users' },
  { href: '/admin/featured', label: 'Featured' },
  { href: '/admin/settings', label: 'Settings' },
  { href: '/admin/jobs', label: 'Jobs' },
  { href: '/admin/lectures', label: 'Lectures' },
]

export default function AdminLayout(props: RouteSectionProps) {
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = createSignal(false)

  const activeHref = createMemo(() => {
    const path = location.pathname
    const match = NAV_ITEMS.find((it) => path === it.href || path.startsWith(`${it.href}/`))
    return match?.href ?? '/admin/users'
  })

  const activeLabel = createMemo(
    () => NAV_ITEMS.find((it) => it.href === activeHref())?.label ?? 'Admin'
  )

  const tabClass = (href: string) =>
    `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
      activeHref() === href
        ? 'bg-muted/50 text-foreground'
        : 'text-muted hover:text-foreground hover:bg-muted/30'
    }`

  return (
    <div class="min-h-0 flex-1">
      <header class="sticky top-0 z-40 border-b border-border/40 bg-background/95 backdrop-blur-sm">
        <div class="container mx-auto px-4">
          <div class="flex items-center justify-between py-4 gap-3">
            <div class="min-w-0">
              <div class="flex items-center gap-3">
                <h1 class="font-display text-2xl text-parchment-100 text-shadow-golden truncate">
                  Admin
                </h1>
                <span class="hidden sm:inline text-muted">/</span>
                <span class="hidden sm:inline font-serif text-parchment-200 truncate">
                  {activeLabel()}
                </span>
              </div>
            </div>

            {/* Desktop tabs */}
            <nav class="hidden md:flex items-center gap-1">
              <For each={NAV_ITEMS}>
                {(item) => (
                  <A href={item.href} class={tabClass(item.href)}>
                    {item.label}
                  </A>
                )}
              </For>
            </nav>

            {/* Mobile menu */}
            <div class="md:hidden">
              <button
                type="button"
                class="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm font-medium hover:bg-muted/30"
                onClick={() => setMobileOpen((v) => !v)}
                aria-expanded={mobileOpen()}
              >
                {activeLabel()}
              </button>
            </div>
          </div>

          <Show when={mobileOpen()}>
            <nav class="md:hidden pb-4">
              <div class="grid grid-cols-2 gap-2">
                <For each={NAV_ITEMS}>
                  {(item) => (
                    <A
                      href={item.href}
                      class={tabClass(item.href)}
                      onClick={() => setMobileOpen(false)}
                    >
                      {item.label}
                    </A>
                  )}
                </For>
              </div>
            </nav>
          </Show>
        </div>
      </header>

      {props.children}
    </div>
  )
}
