import * as Dialog from '@kobalte/core/dialog'
import { For, createEffect, createSignal, onMount } from 'solid-js'
import { Button } from './ui'

type Theme = 'dark-academia' | 'vaporwave' | 'cosmic-horror' | 'techno-occult'

interface ThemeOption {
  value: Theme
  label: string
  description: string
  primaryColor: string
  accentColor: string
}

const themeOptions: ThemeOption[] = [
  {
    value: 'dark-academia',
    label: 'Dark Academia',
    description: 'Classical elegance with a scholarly aesthetic',
    primaryColor: '#2a241c', // arcanum-950
    accentColor: '#c29747', // parchment-500
  },
  {
    value: 'vaporwave',
    label: 'Vaporwave',
    description: 'Retro-futuristic digital aesthetics',
    primaryColor: '#13186a', // vaporwave-950
    accentColor: '#8656ff', // mystic-500
  },
  {
    value: 'cosmic-horror',
    label: 'Cosmic Horror',
    description: 'Eldritch and otherworldly influences',
    primaryColor: '#170b21',
    accentColor: '#6b0f56',
  },
  {
    value: 'techno-occult',
    label: 'Techno-Occult',
    description: 'Digital mysticism and technological esotericism',
    primaryColor: '#0b1a23',
    accentColor: '#2a9d8f',
  },
]

export function ThemeSwitcher() {
  const [currentTheme, setCurrentTheme] = createSignal<Theme>('dark-academia')
  const [isOpen, setIsOpen] = createSignal(false)

  // Apply theme on mount and when theme changes
  const applyTheme = (theme: Theme) => {
    const root = document.documentElement

    // Reset all theme classes
    themeOptions.forEach((option) => {
      root.classList.remove(`theme-${option.value}`)
    })

    // Add current theme class
    root.classList.add(`theme-${theme}`)

    // Save to localStorage
    localStorage.setItem('arcanum-theme', theme)
  }

  // Initialize theme from localStorage or default
  onMount(() => {
    const savedTheme = localStorage.getItem('arcanum-theme') as Theme | null
    if (savedTheme && themeOptions.some((option) => option.value === savedTheme)) {
      setCurrentTheme(savedTheme)
    }
    applyTheme(currentTheme())
  })

  createEffect(() => {
    applyTheme(currentTheme())
  })

  const getCurrentTheme = () => {
    return themeOptions.find((option) => option.value === currentTheme()) || themeOptions[0]
  }

  return (
    <div class="fixed bottom-4 right-4 z-50">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        class="rounded-full w-10 h-10 p-0 flex items-center justify-center"
      >
        <span class="sr-only">Change Theme</span>
        <div
          class="w-6 h-6 rounded-full border-2 border-parchment-300"
          style={{ 'background-color': getCurrentTheme().accentColor }}
        />
      </Button>

      <Dialog.Root open={isOpen()} onOpenChange={setIsOpen}>
        <Dialog.Portal>
          <Dialog.Overlay class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />

          <Dialog.Content class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 bg-arcanum-900 border border-parchment-700/30 rounded shadow-arcane p-6">
            <Dialog.Title class="text-xl font-display text-parchment-100 mb-4">
              Select Theme
            </Dialog.Title>

            <Dialog.Description class="text-sm font-serif text-parchment-300 mb-6">
              Choose an aesthetic that matches your scholarly pursuits.
            </Dialog.Description>

            <div class="space-y-4">
              <For each={themeOptions}>
                {(theme) => (
                  <div
                    class={`p-4 rounded cursor-pointer border transition-all ${
                      currentTheme() === theme.value
                        ? 'border-parchment-400 bg-arcanum-800'
                        : 'border-parchment-800/30 hover:border-parchment-700/50'
                    }`}
                    onClick={() => setCurrentTheme(theme.value)}
                  >
                    <div class="flex items-center">
                      <div
                        class="w-8 h-8 rounded-full border border-parchment-600/30"
                        style={{
                          'background-image': `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`,
                        }}
                      />
                      <div class="ml-3">
                        <h3 class="text-parchment-100 font-serif">{theme.label}</h3>
                        <p class="text-xs text-parchment-400">{theme.description}</p>
                      </div>
                    </div>
                  </div>
                )}
              </For>
            </div>

            <div class="mt-6 flex justify-end gap-2">
              <Dialog.CloseButton>
                <Button variant="ghost" size="sm">
                  Cancel
                </Button>
              </Dialog.CloseButton>

              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  applyTheme(currentTheme())
                  setIsOpen(false)
                }}
              >
                Apply Theme
              </Button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  )
}
