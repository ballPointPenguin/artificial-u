# Internationalization (i18n) Guide

This directory contains the internationalization setup for the Artificial University frontend.

## Overview

We use `@solid-primitives/i18n` for text translations. The system is designed to:
- Support multiple languages (currently English only)
- Provide type-safe translation keys
- Enable easy locale switching
- Support future expansion to Spanish, Chinese, and other languages

## Structure

```
i18n/
├── index.tsx           # i18n provider, hooks, and setup
├── locales/
│   ├── en.ts          # English translations
│   └── es.ts          # Spanish translations (future)
└── README.md          # This file
```

## Usage

### 1. Using Translations in Components

Import the `useTranslations` hook and access translation strings:

```tsx
import { useTranslations } from '../i18n'

function MyComponent() {
  const t = useTranslations()

  return (
    <div>
      <h1>{t.home.hero.title}</h1>
      <p>{t.home.hero.subtitle}</p>
    </div>
  )
}
```

### 2. Switching Locales

Use the `useLocale` hook to access and change the current locale:

```tsx
import { useLocale } from '../i18n'

function LanguageSwitcher() {
  const { currentLocale, setLocale } = useLocale()

  return (
    <button onClick={() => setLocale('es')}>
      Current: {currentLocale()}
    </button>
  )
}
```

Or use the pre-built `LocaleSwitcher` component:

```tsx
import { LocaleSwitcher } from '../components/LocaleSwitcher'

function NavBar() {
  return (
    <nav>
      {/* ... other nav items ... */}
      <LocaleSwitcher />
    </nav>
  )
}
```

### 3. Adding a New Language

To add a new language (e.g., Spanish):

**Step 1:** Create the locale file `web/src/i18n/locales/es.ts`:

```typescript
import type { Locale } from './en'

export const es: Locale = {
  site: {
    name: 'UNIVERSIDAD ARTIFICIAL',
    shortName: 'A|U',
  },
  nav: {
    about: 'Acerca de',
    academics: 'Académicos',
    // ... translate all keys from en.ts
  },
  // ... continue translating
}
```

**Step 2:** Update `web/src/i18n/index.tsx`:

```typescript
import { es } from './locales/es'

export type LocaleCode = 'en' | 'es'  // Add 'es'

const locales: Record<LocaleCode, Locale> = {
  en,
  es,  // Add Spanish locale
}
```

**Step 3:** Update `LocaleSwitcher.tsx` to show the new language option:

```typescript
const availableLocales = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },  // Uncomment
]
```

### 4. Adding New Translation Keys

When adding new UI text:

**Step 1:** Add the key to `locales/en.ts`:

```typescript
export const en = {
  // ... existing keys ...

  newFeature: {
    title: 'New Feature',
    description: 'This is a new feature',
  },
}
```

**Step 2:** Use the new key in your component:

```tsx
const t = useTranslations()
return <h2>{t.newFeature.title}</h2>
```

**Step 3:** TypeScript will ensure all locales have the same structure.

## Best Practices

1. **Organize by Feature**: Group related translations under feature namespaces (e.g., `home`, `nav`, `about`)

2. **Use Descriptive Keys**: Make translation keys self-documenting
   ```typescript
   // Good
   common.buttons.save

   // Avoid
   common.btn1
   ```

3. **Keep Strings in Locale Files**: Never hardcode user-facing text in components

4. **Type Safety**: TypeScript enforces that all locales have the same structure as the English locale

5. **Context in Comments**: Add comments for strings that might need cultural context
   ```typescript
   welcome: 'Welcome!',  // Greeting shown on first visit
   ```

## Implementation Details

- **Provider**: `I18nProvider` wraps the app in `web/src/index.tsx`
- **Reactive**: Locale changes trigger component re-renders automatically
- **Type-safe**: All translation keys are typed based on the English locale
- **Persistence**: TODO - Currently locale choice is not persisted to localStorage

## Future Enhancements

- [ ] Persist locale selection to localStorage
- [ ] Add Spanish (es) translations
- [ ] Add Chinese (zh) translations
- [ ] Support RTL languages (Arabic, Hebrew)
- [ ] Date/time formatting per locale
- [ ] Number formatting per locale
- [ ] Pluralization support
- [ ] Lazy loading of locale files

## Resources

- [@solid-primitives/i18n Documentation](https://primitives.solidjs.community/package/i18n/)
- [SolidJS Documentation](https://www.solidjs.com/)
