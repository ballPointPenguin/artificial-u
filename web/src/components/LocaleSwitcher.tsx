import { For } from 'solid-js'
import { useLocale, type LocaleCode } from '../i18n'

/**
 * Locale Switcher Component
 *
 * Displays a dropdown or buttons to switch between available locales.
 * Currently only supports English, but designed for easy expansion.
 */
export function LocaleSwitcher() {
  const { currentLocale, setLocale } = useLocale()

  const availableLocales: Array<{ code: LocaleCode; name: string; flag: string }> = [
    { code: 'en', name: 'English', flag: '🇺🇸' },
    // { code: 'es', name: 'Español', flag: '🇪🇸' },  // Future
    // { code: 'zh', name: '中文', flag: '🇨🇳' },     // Future
  ]

  // Only show the switcher if there's more than one locale
  if (availableLocales.length <= 1) {
    return null
  }

  return (
    <div class="flex items-center gap-2">
      <For each={availableLocales}>
        {(locale) => (
          <button
            type="button"
            onClick={() => setLocale(locale.code)}
            class={`px-3 py-1 rounded font-serif text-sm transition-colors ${
              currentLocale() === locale.code
                ? 'bg-parchment-300 text-arcanum-900'
                : 'bg-arcanum-800 text-parchment-200 hover:bg-arcanum-700'
            }`}
            title={locale.name}
          >
            <span aria-label={locale.name}>{locale.flag}</span>
            <span class="ml-1 hidden md:inline">{locale.name}</span>
          </button>
        )}
      </For>
    </div>
  )
}
