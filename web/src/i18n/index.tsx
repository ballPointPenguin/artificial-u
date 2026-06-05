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
 * Content language codes — languages for which generated content exists.
 * Distinct from the UI locale: a user can browse in Spanish but read English content.
 */
export type ContentLanguage = 'en' | 'fr'

export const SUPPORTED_CONTENT_LANGUAGES: readonly ContentLanguage[] = ['en', 'fr']

const CONTENT_LANGUAGE_STORAGE_KEY = 'au-content-language'

/** Map a UI locale to the closest supported content language, falling back to 'en'. */
function toContentLanguage(locale: LocaleCode): ContentLanguage {
  return (SUPPORTED_CONTENT_LANGUAGES as readonly string[]).includes(locale)
    ? (locale as ContentLanguage)
    : 'en'
}

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
  contentLanguage: () => ContentLanguage
  contentLanguageOverride: () => ContentLanguage | null
  /** Pass null to clear the override and auto-follow the UI locale. */
  setContentLanguage: (lang: ContentLanguage | null) => void
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

  // Content language: explicit override takes precedence; otherwise follow the UI locale.
  const getInitialContentLanguageOverride = (): ContentLanguage | null => {
    if (typeof window === 'undefined') return null
    const stored = localStorage.getItem(CONTENT_LANGUAGE_STORAGE_KEY)
    return stored && (SUPPORTED_CONTENT_LANGUAGES as readonly string[]).includes(stored)
      ? (stored as ContentLanguage)
      : null
  }

  const [contentLanguageOverride, setContentLanguageOverrideSignal] =
    createSignal<ContentLanguage | null>(getInitialContentLanguageOverride())

  const contentLanguage = createMemo<ContentLanguage>(
    () => contentLanguageOverride() ?? toContentLanguage(currentLocale())
  )

  const setContentLanguage = (lang: ContentLanguage | null) => {
    setContentLanguageOverrideSignal(lang)
    if (typeof window !== 'undefined') {
      if (lang === null) {
        localStorage.removeItem(CONTENT_LANGUAGE_STORAGE_KEY)
      } else {
        localStorage.setItem(CONTENT_LANGUAGE_STORAGE_KEY, lang)
      }
    }
  }

  const contextValue = {
    t, // Return the memo directly for reactivity
    currentLocale,
    setLocale: (locale: LocaleCode) => {
      setCurrentLocale(locale)
      if (typeof window !== 'undefined') {
        localStorage.setItem(LOCALE_STORAGE_KEY, locale)
      }
    },
    contentLanguage,
    contentLanguageOverride,
    setContentLanguage,
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

/**
 * Hook to access and override the content language.
 *
 * The content language defaults to the UI locale when that locale has a matching
 * content sandbox (e.g. 'fr' UI → 'fr' content). For unsupported UI locales
 * (e.g. 'es', 'zh') it falls back to 'en'. Users can explicitly pin a content
 * language from their profile to decouple it from the UI locale.
 *
 * @example
 * const { contentLanguage, setContentLanguage } = useContentLanguage()
 * // contentLanguage() → 'en' | 'fr'
 * // setContentLanguage('fr')   — explicit override
 * // setContentLanguage(null)   — clear override, auto-follow UI locale again
 */
export function useContentLanguage() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useContentLanguage must be used within I18nProvider')
  }
  return {
    contentLanguage: context.contentLanguage,
    contentLanguageOverride: context.contentLanguageOverride,
    setContentLanguage: context.setContentLanguage,
  }
}
