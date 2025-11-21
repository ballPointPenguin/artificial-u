import { createContext, createMemo, createSignal, type ParentComponent, useContext } from 'solid-js'
import { en, type Locale } from './locales/en'

/**
 * Available locale codes
 */
export type LocaleCode = 'en' // | 'es' | 'zh' - add more as needed

/**
 * Dictionary of all available locales
 */
const locales: Record<LocaleCode, Locale> = {
  en,
  // es: () => import('./locales/es').then(m => m.es),  // Lazy load in future
  // zh: () => import('./locales/zh').then(m => m.zh),
}

/**
 * Context for i18n
 */
const I18nContext = createContext<{
  t: Locale
  currentLocale: () => LocaleCode
  setLocale: (locale: LocaleCode) => void
}>()

/**
 * I18n Provider component that wraps the app
 */
export const I18nProvider: ParentComponent = (props) => {
  // TODO: Load from localStorage or user preferences
  const defaultLocale: LocaleCode = 'en'

  const [currentLocale, setCurrentLocale] = createSignal<LocaleCode>(defaultLocale)

  // Create reactive dictionary based on current locale
  const t = createMemo(() => locales[currentLocale()])

  const contextValue = {
    get t() {
      return t()
    },
    currentLocale,
    setLocale: (locale: LocaleCode) => {
      setCurrentLocale(locale)
      // TODO: Persist to localStorage
    },
  }

  return <I18nContext.Provider value={contextValue}>{props.children}</I18nContext.Provider>
}

/**
 * Hook to access translations
 *
 * @example
 * const t = useTranslations()
 * return <h1>{t.home.hero.title}</h1>
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
