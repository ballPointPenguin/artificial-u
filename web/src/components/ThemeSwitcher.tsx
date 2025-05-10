import * as Dialog from '@kobalte/core/dialog'
import { For, createSignal } from 'solid-js'
import { hslStringToCss } from '../utils/colors'
import { currentThemeProperties, setTheme, theme, themeProperties } from '../utils/theme'
import { Button } from './ui'

type ThemeValue = 'dark-academia' | 'vaporwave' | 'wabi-sabi' | 'biophilia'

interface ThemeOption {
  value: ThemeValue
  label: string
  description: string
  previewSurfaceColor: string // HSL string from themeProperties
  previewPrimaryColor: string // HSL string from themeProperties
}

const themeOptionValues: ThemeValue[] = ['dark-academia', 'vaporwave', 'wabi-sabi', 'biophilia']

const themeOptions: ThemeOption[] = themeOptionValues.map((mode) => {
  const properties = themeProperties[mode]
  let description = ''
  let label = ''

  // Descriptions can be centralized or managed elsewhere if they grow complex
  switch (mode) {
    case 'dark-academia':
      label = 'Dark Academia'
      description = 'Classical elegance with a scholarly aesthetic'
      break
    case 'vaporwave':
      label = 'Vaporwave'
      description = 'Retro-futuristic digital aesthetics'
      break
    case 'wabi-sabi':
      label = 'Wabi Sabi'
      description = 'Embracing imperfection and natural simplicity'
      break
    case 'biophilia':
      label = 'Biophilia'
      description = 'Lush greens, floral pops, and natural textures'
      break
    default:
      // Optional: handle any unexpected mode
      label = 'Unknown Theme'
      description = 'No description available.'
      break
  }

  return {
    value: mode,
    label,
    description,
    previewSurfaceColor: properties.surfaceColor,
    previewPrimaryColor: properties.primaryColor,
  }
})

export function ThemeSwitcher() {
  const [isOpen, setIsOpen] = createSignal(false)

  return (
    <div class="fixed bottom-4 right-4 z-50">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        class="rounded-full w-10 h-10 p-0 flex items-center justify-center shadow-lg hover:ring-2 hover:ring-primary/50 transition-all duration-300"
        aria-label="Change theme"
        title={`Current theme: ${themeOptions.find((opt) => opt.value === theme())?.label || 'Unknown'}`}
      >
        <div
          class="w-6 h-6 rounded-full border-2 transition-colors duration-300"
          style={{
            'background-color': hslStringToCss(currentThemeProperties.properties.primaryColor),
            'border-color': hslStringToCss(currentThemeProperties.properties.accentColor),
          }}
        />
      </Button>

      <Dialog.Root open={isOpen()} onOpenChange={setIsOpen}>
        <Dialog.Portal>
          <Dialog.Overlay class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 transition-opacity duration-300" />
          <Dialog.Content
            class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 bg-surface border border-border rounded-lg shadow-arcane p-6 transition-all duration-300 focus:outline-none"
            aria-labelledby="theme-dialog-title"
          >
            <Dialog.Title id="theme-dialog-title" class="text-xl font-display text-foreground mb-1">
              Select Theme
            </Dialog.Title>
            <Dialog.Description class="text-sm font-serif text-muted mb-5">
              Choose an aesthetic that matches your scholarly pursuits.
            </Dialog.Description>

            <div role="radiogroup" class="space-y-3">
              <For each={themeOptions}>
                {(option) => (
                  <div
                    class={`p-3.5 rounded-md cursor-pointer border transition-all duration-200 ease-in-out flex items-center group focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-surface focus:ring-primary
                      ${
                        theme() === option.value
                          ? 'border-primary ring-2 ring-primary bg-primary/5 shadow-md' // Active state
                          : 'border-border hover:border-primary/60 bg-surface/60 hover:bg-surface opacity-80 hover:opacity-100' // Inactive state
                      }`}
                    onClick={() => setTheme(option.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        setTheme(option.value)
                      }
                    }}
                    tabindex="0"
                    role="radio"
                    aria-checked={theme() === option.value}
                    aria-label={option.label}
                  >
                    <div
                      class="w-8 h-8 rounded-full border border-black/10 dark:border-white/10 shadow-inner mr-3.5 shrink-0"
                      style={{
                        'background-image': `linear-gradient(135deg, ${hslStringToCss(
                          option.previewSurfaceColor
                        )}, ${hslStringToCss(option.previewPrimaryColor)})`,
                      }}
                      aria-hidden="true"
                    />
                    <div class="flex-grow">
                      <h3 class="font-semibold text-foreground group-hover:text-primary transition-colors">
                        {option.label}
                      </h3>
                      <p class="text-xs text-muted font-serif group-hover:text-primary/80 transition-colors">
                        {option.description}
                      </p>
                    </div>
                    {theme() === option.value && (
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        class="w-5 h-5 text-primary ml-auto shrink-0 opacity-80"
                        aria-hidden="true"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                          clip-rule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                )}
              </For>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  )
}
