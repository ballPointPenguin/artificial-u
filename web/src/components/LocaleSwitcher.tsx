import { For, Show } from 'solid-js'
import { type LocaleCode, useLocale } from '../i18n'

/**
 * Locale Switcher Component
 *
 * Displays a dropdown or buttons to switch between available locales.
 * Currently only supports English, but designed for easy expansion.
 */
export function LocaleSwitcher() {
  const { currentLocale, setLocale } = useLocale()

  const availableLocales: Array<{ code: LocaleCode; name: string; flag: string }> = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    // { code: 'es', name: 'Español', flag: '🇪🇸' },  // Future
    // { code: 'zh', name: '中文', flag: '🇨🇳' },     // Future
  ]

  // Only show the switcher if there's more than one locale
  return (
    <Show when={availableLocales.length > 1}>
      <div class="flex items-center gap-2">
        <For each={availableLocales}>
          {(locale) => {
            // This comparison is necessary for when multiple locales are added
            const isActive = () =>
              // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
              currentLocale() === locale.code
            return (
              <button
                type="button"
                onClick={() => {
                  setLocale(locale.code)
                }}
                class={`px-3 py-1 rounded font-serif text-sm transition-colors ${
                  isActive()
                    ? 'bg-parchment-300 text-arcanum-900'
                    : 'bg-arcanum-800 text-parchment-200 hover:bg-arcanum-700'
                }`}
                title={locale.name}
              >
                <span aria-label={locale.name}>{locale.flag}</span>
                <span class="ml-1 hidden md:inline">{locale.name}</span>
              </button>
            )
          }}
        </For>
      </div>
    </Show>
  )
}
