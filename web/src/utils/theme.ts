import { createEffect, createSignal } from 'solid-js'
import { createStore } from 'solid-js/store'

// Theme types
export type ThemeMode = 'dark-academia' | 'vaporwave' | 'cosmic-horror' | 'techno-occult'

// Extend ThemeProperties for status colors
interface ThemeProperties {
  primaryColor: string
  secondaryColor: string
  accentColor: string
  backgroundColor: string
  textColor: string
  borderColor: string
  surfaceColor: string
  // Status Colors (using HSL strings)
  infoColor: string
  infoBgColor: string
  infoBorderColor: string
  successColor: string
  successBgColor: string
  successBorderColor: string
  warningColor: string
  warningBgColor: string
  warningBorderColor: string
  dangerColor: string
  dangerBgColor: string
  dangerBorderColor: string
}

// Placeholder HSL values - these need refinement!
const statusPlaceholders = {
  info: { color: '217deg 89% 70%', bg: '217deg 89% 20%', border: '217deg 89% 40%' }, // Blueish
  success: { color: '145deg 75% 70%', bg: '145deg 75% 15%', border: '145deg 75% 35%' }, // Greenish
  warning: { color: '39deg 100% 70%', bg: '39deg 100% 15%', border: '39deg 100% 40%' }, // Orangey
  danger: { color: '0deg 84% 70%', bg: '0deg 84% 15%', border: '0deg 84% 40%' }, // Reddish
}

// Theme configuration
const themeProperties: Record<ThemeMode, ThemeProperties> = {
  'dark-academia': {
    primaryColor: '39deg 50% 52%', // Was #c29747
    secondaryColor: '255deg 100% 67%', // Was #8656ff
    accentColor: '30deg 23% 60%', // Was #b09981
    backgroundColor: '31deg 18% 13%', // Was #2a241c
    textColor: '38deg 33% 95%', // Was #f8f5f0
    borderColor: '30deg 25% 28%', // Was #594936
    surfaceColor: '30deg 22% 23%',
    infoColor: statusPlaceholders.info.color,
    infoBgColor: statusPlaceholders.info.bg,
    infoBorderColor: statusPlaceholders.info.border,
    successColor: statusPlaceholders.success.color,
    successBgColor: statusPlaceholders.success.bg,
    successBorderColor: statusPlaceholders.success.border,
    warningColor: statusPlaceholders.warning.color,
    warningBgColor: statusPlaceholders.warning.bg,
    warningBorderColor: statusPlaceholders.warning.border,
    dangerColor: statusPlaceholders.danger.color,
    dangerBgColor: statusPlaceholders.danger.bg,
    dangerBorderColor: statusPlaceholders.danger.border,
  },
  vaporwave: {
    primaryColor: '255deg 100% 67%', // Was #8656ff
    secondaryColor: '212deg 99% 84%', // Was #b0cafe
    accentColor: '276deg 98% 79%', // Was #d097fe
    backgroundColor: '236deg 71% 25%', // Was #13186a
    textColor: '216deg 100% 97%', // Was #f3f8ff
    borderColor: '254deg 69% 43%', // Was #4322bd
    surfaceColor: '236deg 71% 30%',
    infoColor: statusPlaceholders.info.color,
    infoBgColor: statusPlaceholders.info.bg,
    infoBorderColor: statusPlaceholders.info.border,
    successColor: statusPlaceholders.success.color,
    successBgColor: statusPlaceholders.success.bg,
    successBorderColor: statusPlaceholders.success.border,
    warningColor: statusPlaceholders.warning.color,
    warningBgColor: statusPlaceholders.warning.bg,
    warningBorderColor: statusPlaceholders.warning.border,
    dangerColor: statusPlaceholders.danger.color,
    dangerBgColor: statusPlaceholders.danger.bg,
    dangerBorderColor: statusPlaceholders.danger.border,
  },
  'cosmic-horror': {
    primaryColor: '314deg 73% 24%', // Was #6b0f56
    secondaryColor: '191deg 65% 27%', // Was #186272
    accentColor: '325deg 58% 39%', // Was #9f2b68
    backgroundColor: '279deg 53% 9%', // Was #170b21
    textColor: '240deg 21% 95%', // Was #ededf5
    borderColor: '299deg 39% 23%', // Was #522453
    surfaceColor: '279deg 53% 14%',
    infoColor: statusPlaceholders.info.color,
    infoBgColor: statusPlaceholders.info.bg,
    infoBorderColor: statusPlaceholders.info.border,
    successColor: statusPlaceholders.success.color,
    successBgColor: statusPlaceholders.success.bg,
    successBorderColor: statusPlaceholders.success.border,
    warningColor: statusPlaceholders.warning.color,
    warningBgColor: statusPlaceholders.warning.bg,
    warningBorderColor: statusPlaceholders.warning.border,
    dangerColor: statusPlaceholders.danger.color,
    dangerBgColor: statusPlaceholders.danger.bg,
    dangerBorderColor: statusPlaceholders.danger.border,
  },
  'techno-occult': {
    primaryColor: '173deg 57% 39%', // Was #2a9d8f
    secondaryColor: '44deg 74% 66%', // Was #e9c46a
    accentColor: '289deg 45% 26%', // Was #592463
    backgroundColor: '203deg 56% 9%', // Was #0b1a23
    textColor: '197deg 38% 95%', // Was #eff6f8
    borderColor: '200deg 35% 19%', // Was #203842
    surfaceColor: '203deg 56% 14%',
    infoColor: statusPlaceholders.info.color,
    infoBgColor: statusPlaceholders.info.bg,
    infoBorderColor: statusPlaceholders.info.border,
    successColor: statusPlaceholders.success.color,
    successBgColor: statusPlaceholders.success.bg,
    successBorderColor: statusPlaceholders.success.border,
    warningColor: statusPlaceholders.warning.color,
    warningBgColor: statusPlaceholders.warning.bg,
    warningBorderColor: statusPlaceholders.warning.border,
    dangerColor: statusPlaceholders.danger.color,
    dangerBgColor: statusPlaceholders.danger.bg,
    dangerBorderColor: statusPlaceholders.danger.border,
  },
}

// Create a reactive theme store
function createThemeStoreInternal() {
  // Get theme from localStorage or use default
  const getInitialTheme = (): ThemeMode => {
    if (typeof window === 'undefined') return 'dark-academia'

    const savedTheme = localStorage.getItem('arcanum-theme') as ThemeMode | null
    return savedTheme && Object.keys(themeProperties).includes(savedTheme)
      ? savedTheme
      : 'dark-academia'
  }

  const [theme, setTheme] = createSignal<ThemeMode>(getInitialTheme())

  // Initialize with default values
  const initialTheme = getInitialTheme()
  const [store, setStore] = createStore({
    current: initialTheme,
    properties: themeProperties[initialTheme],
  })

  // Update theme properties when theme changes
  createEffect(() => {
    setStore({
      current: theme(),
      properties: themeProperties[theme()],
    })

    // Update DOM
    applyThemeToDOM(theme())

    // Save to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('arcanum-theme', theme())
    }
  })

  return {
    theme,
    setTheme,
    store,
  }
}

// Create and export the singleton instance of the theme store
const themeStore = createThemeStoreInternal()
export const theme = themeStore.theme
export const setTheme = themeStore.setTheme
export const currentThemeProperties = themeStore.store // Exporting the reactive properties if needed

// Apply theme to DOM
function applyThemeToDOM(theme: ThemeMode) {
  if (typeof document === 'undefined') return

  const root = document.documentElement

  // Remove all theme classes
  Object.keys(themeProperties).forEach((themeName) => {
    root.classList.remove(`theme-${themeName}`)
  })

  // Add current theme class
  root.classList.add(`theme-${theme}`)

  // glowColor is no longer set by JS
  // const properties = themeProperties[theme] // This line would now cause an error if properties.glowColor was accessed
  // root.style.setProperty('--color-glow', properties.glowColor) // Removed
}

// Helper function to get CSS variable value
export function getThemeVariable(variableName: string): string {
  if (typeof window === 'undefined') return ''

  return getComputedStyle(document.documentElement).getPropertyValue(`--${variableName}`).trim()
}

// Create custom CSS with current theme
export function generateThemeCSS(themeMode: ThemeMode): string {
  const properties = themeProperties[themeMode]
  if (!properties) return ''

  return `
    :root { /* Or a specific theme class if not overriding globally */
      --color-primary: ${properties.primaryColor};
      --color-secondary: ${properties.secondaryColor};
      --color-accent: ${properties.accentColor};
      --color-background: ${properties.backgroundColor};
      --color-text: ${properties.textColor};
      --color-border: ${properties.borderColor};
      --color-surface: ${properties.surfaceColor};
      /* Add status colors here */
      --color-info: ${properties.infoColor};
      --color-info-bg: ${properties.infoBgColor};
      --color-info-border: ${properties.infoBorderColor};
      --color-success: ${properties.successColor};
      --color-success-bg: ${properties.successBgColor};
      --color-success-border: ${properties.successBorderColor};
      --color-warning: ${properties.warningColor};
      --color-warning-bg: ${properties.warningBgColor};
      --color-warning-border: ${properties.warningBorderColor};
      --color-danger: ${properties.dangerColor};
      --color-danger-bg: ${properties.dangerBgColor};
      --color-danger-border: ${properties.dangerBorderColor};
    }
  `
}

// Generate color palette from base color
export function generatePalette(baseColor: string, steps = 10): string[] {
  const palette: string[] = []

  // Simple implementation - in a real app, use a color library
  // This is a placeholder for demonstration purposes
  for (let i = 0; i < steps; i++) {
    // Adjust opacity to create a simple palette
    const opacity = 0.1 + (i * 0.9) / steps
    palette.push(
      `${baseColor}${Math.round(opacity * 255)
        .toString(16)
        .padStart(2, '0')}`
    )
  }

  return palette
}

// Create cosmic wisp background styles
export function createCosmicWispStyles(primaryColor: string, secondaryColor: string): string {
  return `
    background-image:
      radial-gradient(circle at 20% 30%, ${primaryColor}26, transparent 40%),
      radial-gradient(circle at 70% 60%, ${secondaryColor}1a, transparent 50%);
    position: relative;
  `
}
