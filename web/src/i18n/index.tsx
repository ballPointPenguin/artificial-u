import { createContext, createMemo, createSignal, type ParentComponent, useContext } from 'solid-js'
import { en, type Locale } from './locales/en'
import { es } from './locales/es'
import { fr } from './locales/fr'
import { zh } from './locales/zh'

/**
 * Available locale codes
 */
export type LocaleCode = 'en' | 'es' | 'fr' | 'zh'

/**
 * Dictionary of all available locales
 */
const locales: Record<LocaleCode, Locale> = {
  en,
  es,
  fr,
  zh,
}

/**
 * Context for i18n
 */
const I18nContext = createContext<{
  t: () => Locale
  currentLocale: () => LocaleCode
  setLocale: (locale: LocaleCode) => void
}>()

const LOCALE_STORAGE_KEY = 'au-locale'

/**
 * Get the initial locale from localStorage or browser/default
 */
function getInitialLocale(): LocaleCode {
  // Try localStorage first
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (stored && (stored === 'en' || stored === 'es' || stored === 'fr' || stored === 'zh')) {
      return stored
    }

    // Try browser language
    const browserLang = navigator.language.toLowerCase()
    if (browserLang.startsWith('es')) return 'es'
    if (browserLang.startsWith('fr')) return 'fr'
    if (browserLang.startsWith('zh')) return 'zh'
  }

  // Default to English
  return 'en'
}

/**
 * I18n Provider component that wraps the app
 */
export const I18nProvider: ParentComponent = (props) => {
  const [currentLocale, setCurrentLocale] = createSignal<LocaleCode>(getInitialLocale())

  // Create reactive dictionary based on current locale
  const t = createMemo(() => locales[currentLocale()])

  const contextValue = {
    t, // Return the memo directly for reactivity
    currentLocale,
    setLocale: (locale: LocaleCode) => {
      setCurrentLocale(locale)
      // Persist to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(LOCALE_STORAGE_KEY, locale)
      }
    },
  }

  return <I18nContext.Provider value={contextValue}>{props.children}</I18nContext.Provider>
}

/**
 * Hook to access translations
 *
 * @example
 * const t = useTranslations()
 * return <h1>{t().home.hero.title}</h1>
 */
export function useTranslations() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useTranslations must be used within I18nProvider')
  }
  return context.t
}

/**
 * Hook to access locale switching
 *
 * @example
 * const { currentLocale, setLocale } = useLocale()
 * return <button onClick={() => setLocale('es')}>Español</button>
 */
export function useLocale() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useLocale must be used within I18nProvider')
  }
  return { currentLocale: context.currentLocale, setLocale: context.setLocale }
}

/**
 * Combined hook for translations and locale management
 *
 * @example
 * const { t, currentLocale, setLocale } = useI18n()
 * return <h1>{t().home.hero.title}</h1>
 */
export function useI18n() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider')
  }
  return context
}
