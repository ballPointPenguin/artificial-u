import { For } from 'solid-js'
import { type LocaleCode, useLocale } from '../i18n'

/**
 * Locale Switcher Component
 *
 * Displays a compact dropdown on md+ screens and buttons on mobile.
 * Supports English, Spanish, French, and Chinese.
 */
export function LocaleSwitcher() {
  const { currentLocale, setLocale } = useLocale()

  const availableLocales: Array<{ code: LocaleCode; name: string; flag: string }> = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'es', name: 'Español', flag: '🇪🇸' },
    { code: 'fr', name: 'Français', flag: '🇫🇷' },
    { code: 'zh', name: '中文', flag: '🇨🇳' },
  ]

  const handleChange = (e: Event) => {
    const target = e.target as HTMLSelectElement
    setLocale(target.value as LocaleCode)
  }

  return (
    <>
      {/* Mobile: Button layout */}
      <div class="flex md:hidden items-center gap-1">
        <For each={availableLocales}>
          {(locale) => {
            const isActive = () => currentLocale() === locale.code
            return (
              <button
                type="button"
                onClick={() => {
                  setLocale(locale.code)
                }}
                class={`px-2 py-1 rounded text-xs font-serif transition-all duration-200 ${
                  isActive()
                    ? 'bg-primary text-on-primary shadow-sm'
                    : 'bg-surface/50 text-muted hover:bg-surface hover:text-foreground'
                }`}
                title={locale.name}
                aria-label={`Switch to ${locale.name}`}
                aria-pressed={isActive()}
              >
                <span aria-hidden="true">{locale.flag}</span>
              </button>
            )
          }}
        </For>
      </div>

      {/* Desktop: Compact dropdown */}
      <div class="hidden md:block relative">
        <div class="relative inline-flex items-center">
          <select
            value={currentLocale()}
            onChange={handleChange}
            class="appearance-none px-7 py-1 rounded text-xs font-serif bg-surface/50 text-foreground border border-border/30 hover:bg-surface hover:border-border/50 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all duration-200 cursor-pointer"
            aria-label="Select language"
          >
            <For each={availableLocales}>
              {(locale) => (
                <option value={locale.code}>
                  {locale.flag} {locale.name}
                </option>
              )}
            </For>
          </select>
          <svg
            class="absolute right-1.5 w-4 h-4 pointer-events-none text-muted"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>
    </>
  )
}
