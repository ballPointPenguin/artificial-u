import { createEffect, createSignal } from 'solid-js'
import { createStore } from 'solid-js/store'

// Theme types
export type ThemeMode = 'dark-academia' | 'vaporwave' | 'cosmic-horror' | 'techno-occult'

interface ThemeProperties {
  primaryColor: string
  secondaryColor: string
  accentColor: string
  backgroundColor: string
  textColor: string
  borderColor: string
  glowColor: string
}

// Theme configuration
const themeProperties: Record<ThemeMode, ThemeProperties> = {
  'dark-academia': {
    primaryColor: '#c29747', // parchment-500
    secondaryColor: '#8656ff', // mystic-500
    accentColor: '#b09981', // arcanum-400
    backgroundColor: '#2a241c', // arcanum-950
    textColor: '#f8f5f0', // parchment-50
    borderColor: '#594936', // arcanum-800
    glowColor: 'rgba(138, 43, 226, 0.3)',
  },
  vaporwave: {
    primaryColor: '#8656ff', // mystic-500
    secondaryColor: '#b0cafe', // vaporwave-300
    accentColor: '#d097fe', // nebula-400
    backgroundColor: '#13186a', // vaporwave-950
    textColor: '#f3f8ff', // vaporwave-50
    borderColor: '#4322bd', // vaporwave-800
    glowColor: 'rgba(134, 86, 255, 0.3)',
  },
  'cosmic-horror': {
    primaryColor: '#6b0f56',
    secondaryColor: '#186272',
    accentColor: '#9f2b68',
    backgroundColor: '#170b21',
    textColor: '#ededf5',
    borderColor: '#522453',
    glowColor: 'rgba(107, 15, 86, 0.3)',
  },
  'techno-occult': {
    primaryColor: '#2a9d8f',
    secondaryColor: '#e9c46a',
    accentColor: '#592463',
    backgroundColor: '#0b1a23',
    textColor: '#eff6f8',
    borderColor: '#203842',
    glowColor: 'rgba(42, 157, 143, 0.3)',
  },
}

// Create a reactive theme store
export function createThemeStore() {
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

  // Optional: Apply CSS variables for theme properties
  const properties = themeProperties[theme]

  root.style.setProperty('--color-primary', properties.primaryColor)
  root.style.setProperty('--color-secondary', properties.secondaryColor)
  root.style.setProperty('--color-accent', properties.accentColor)
  root.style.setProperty('--color-background', properties.backgroundColor)
  root.style.setProperty('--color-text', properties.textColor)
  root.style.setProperty('--color-border', properties.borderColor)
  root.style.setProperty('--color-glow', properties.glowColor)
}

// Helper function to get CSS variable value
export function getThemeVariable(variableName: string): string {
  if (typeof window === 'undefined') return ''

  return getComputedStyle(document.documentElement).getPropertyValue(`--${variableName}`).trim()
}

// Create custom CSS with current theme
export function generateThemeCSS(theme: ThemeMode): string {
  const properties = themeProperties[theme]

  return `
    :root {
      --color-primary: ${properties.primaryColor};
      --color-secondary: ${properties.secondaryColor};
      --color-accent: ${properties.accentColor};
      --color-background: ${properties.backgroundColor};
      --color-text: ${properties.textColor};
      --color-border: ${properties.borderColor};
      --color-glow: ${properties.glowColor};
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
