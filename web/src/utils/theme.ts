import { createEffect, createSignal, createRoot } from 'solid-js'
import { createStore } from 'solid-js/store'

// Theme types
export type ThemeMode = 'dark-academia' | 'vaporwave' | 'wabi-sabi' | 'biophilia'

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

export const themeProperties: Record<ThemeMode, ThemeProperties> = {
  'dark-academia': {
    primaryColor: '35deg 65% 55%', // Richer, slightly more saturated old gold/bronze
    secondaryColor: '210deg 30% 60%', // Muted steel blue (was purple)
    accentColor: '10deg 40% 45%', // Deep terracotta/dark orange
    backgroundColor: '30deg 15% 12%', // Very dark, slightly warm brown
    textColor: '35deg 25% 88%', // Aged paper / parchment
    borderColor: '30deg 15% 25%', // Darker brown border
    surfaceColor: '30deg 15% 18%', // Slightly lighter dark brown for surfaces
    // Status Colors for Dark Academia
    infoColor: '190deg 35% 65%', // Desaturated teal
    infoBgColor: '190deg 30% 20%', // Dark teal background
    infoBorderColor: '190deg 30% 35%', // Muted teal border
    successColor: '90deg 30% 60%', // Muted olive green
    successBgColor: '90deg 25% 18%', // Dark olive background
    successBorderColor: '90deg 25% 30%', // Muted olive border
    warningColor: '30deg 60% 65%', // Burnt orange / amber
    warningBgColor: '30deg 50% 20%', // Dark amber background
    warningBorderColor: '30deg 50% 35%', // Muted amber border
    dangerColor: '0deg 45% 55%', // Dark crimson / deep red
    dangerBgColor: '0deg 40% 18%', // Dark crimson background
    dangerBorderColor: '0deg 40% 30%', // Muted crimson border
  },
  vaporwave: {
    primaryColor: '260deg 100% 70%', // Vibrant Violet
    secondaryColor: '180deg 100% 55%', // Bright Cyan/Teal
    accentColor: '330deg 100% 65%', // Hot Pink/Magenta
    backgroundColor: '240deg 60% 15%', // Deep Indigo/Dark Blue
    textColor: '210deg 100% 95%', // Off-white with a slight blue tint
    borderColor: '250deg 80% 50%', // Saturated dark purple
    surfaceColor: '240deg 50% 22%', // Slightly lighter Indigo for surfaces
    // Status Colors for Vaporwave
    infoColor: '200deg 100% 65%', // Electric Blue
    infoBgColor: '200deg 70% 25%', // Dark electric blue background
    infoBorderColor: '200deg 70% 45%', // Bright electric blue border
    successColor: '120deg 100% 60%', // Neon Green / Lime
    successBgColor: '120deg 70% 20%', // Dark neon green background
    successBorderColor: '120deg 70% 40%', // Bright neon green border
    warningColor: '45deg 100% 60%', // Vivid Orange/Yellow
    warningBgColor: '45deg 70% 22%', // Dark vivid orange background
    warningBorderColor: '45deg 70% 40%', // Bright vivid orange border
    dangerColor: '300deg 100% 60%', // Glitchy Magenta/Purple
    dangerBgColor: '300deg 70% 20%', // Dark magenta background
    dangerBorderColor: '300deg 70% 40%', // Bright magenta border
  },
  'wabi-sabi': {
    primaryColor: '30deg 25% 60%', // Muted terracotta/brown
    secondaryColor: '90deg 10% 70%', // Soft, desaturated grey-green
    accentColor: '40deg 30% 50%', // Muted ochre/gold
    backgroundColor: '35deg 30% 92%', // Light, warm beige
    textColor: '35deg 15% 30%', // Dark, muted brown
    borderColor: '35deg 20% 80%', // Light beige
    surfaceColor: '35deg 30% 88%', // Slightly off-white/beige, darker than bg
    infoColor: '210deg 20% 50%', // Muted blue-grey
    infoBgColor: '210deg 20% 85%', // Very light, desaturated blue-grey
    infoBorderColor: '210deg 20% 70%', // Light, desaturated blue-grey
    successColor: '120deg 25% 45%', // Muted, earthy green
    successBgColor: '120deg 25% 88%', // Very light, desaturated green
    successBorderColor: '120deg 25% 70%', // Light, desaturated green
    warningColor: '40deg 50% 50%', // Muted ochre or amber
    warningBgColor: '40deg 50% 88%', // Very light, desaturated ochre
    warningBorderColor: '40deg 50% 70%', // Light, desaturated ochre
    dangerColor: '15deg 35% 50%', // Muted, desaturated red/terracotta
    dangerBgColor: '15deg 35% 88%', // Very light, desaturated red
    dangerBorderColor: '15deg 35% 70%', // Light, desaturated red
  },
  biophilia: {
    primaryColor: '120deg 60% 45%', // Vibrant Leaf Green
    secondaryColor: '320deg 70% 65%', // Bright Orchid Pink
    accentColor: '50deg 100% 45%', // Deeper Sunny Yellow
    backgroundColor: '90deg 60% 90%', // Light Honeydew
    textColor: '30deg 40% 18%', // Darker, richer Woody Brown
    borderColor: '30deg 25% 50%', // Medium Woody Brown
    surfaceColor: '90deg 55% 94%', // Lighter Honeydew
    infoColor: '210deg 80% 60%',
    infoBgColor: '210deg 80% 92%',
    infoBorderColor: '210deg 80% 75%',
    successColor: '140deg 60% 50%',
    successBgColor: '140deg 60% 90%',
    successBorderColor: '140deg 60% 70%',
    warningColor: '35deg 100% 60%',
    warningBgColor: '35deg 100% 92%',
    warningBorderColor: '35deg 100% 75%',
    dangerColor: '0deg 80% 60%',
    dangerBgColor: '0deg 80% 92%',
    dangerBorderColor: '0deg 80% 75%',
  },
}

// Create a reactive theme store
function createThemeStoreInternal() {
  return createRoot(() => {
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
  })
}

// Create and export the singleton instance of the theme store
const themeStore = createThemeStoreInternal()
export const theme = themeStore.theme
export const setTheme = themeStore.setTheme
// Exporting the reactive properties
export const currentThemeProperties = themeStore.store

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
}

// Helper function to get CSS variable value
export function getThemeVariable(variableName: string): string {
  if (typeof window === 'undefined') return ''

  return getComputedStyle(document.documentElement).getPropertyValue(`--${variableName}`).trim()
}
