import { type JSX, Show, mergeProps, splitProps } from 'solid-js'
import { Button } from './Button'
import './MagicButton.css'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'link'
type ButtonSize = 'sm' | 'md' | 'lg'

interface MagicButtonProps extends Omit<JSX.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: JSX.Element
  isLoading?: boolean
  loadingText?: string
  iconOnly?: boolean
}

export function MagicButton(props: MagicButtonProps) {
  const merged = mergeProps(
    {
      variant: 'secondary' as ButtonVariant,
      size: 'md' as ButtonSize,
      iconOnly: false,
    },
    props
  )

  const [local, others] = splitProps(merged, [
    'class',
    'children',
    'isLoading',
    'loadingText',
    'iconOnly',
  ])

  return (
    <Button {...others} class={`relative overflow-hidden magic-button group ${local.class || ''}`}>
      <span class="relative z-10 flex items-center gap-2">
        <span class="inline-block align-middle magic-icon magic-button-icon">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-5 h-5 transition-transform duration-500 group-hover:rotate-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <title>Magic</title>
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15.5 8.5l-8 8m0 0L3 21l4.5-4.5m0 0l8-8M19 5l.01-.01M15 3l.01-.01M21 9l.01-.01M17 13l.01-.01"
            />
          </svg>
        </span>

        <Show when={!local.iconOnly} fallback={<span class="sr-only">{local.children}</span>}>
          <span>
            <Show
              when={!local.isLoading}
              fallback={
                <span class="flex items-center gap-1">
                  <span class="inline-block w-4 h-4 border-2 rounded-full animate-spin magic-button-spinner" />
                  {local.loadingText || 'Loading...'}
                </span>
              }
            >
              {local.children}
            </Show>
          </span>
        </Show>
      </span>

      <span class="absolute -inset-px rounded overflow-hidden">
        <span class="absolute inset-0 opacity-50 group-hover:opacity-100 transition-opacity duration-500 magic-sparkle-overlay" />

        {/* Temporarily make pulse-1 always visible and not pulsing for diagnosis */}
        <span class="absolute h-10 w-10 -top-5 -left-5 rounded-full blur-xl transform scale-100 transition-transform duration-700 magic-sparkle-pulse-1" />

        <span class="absolute h-8 w-8 -bottom-4 -right-4 rounded-full blur-lg transform scale-0 group-hover:scale-100 group-hover:animate-pulse transition-transform duration-700 delay-100 magic-sparkle-pulse-2" />

        {/* Temporarily make shimmer always visible and animating for diagnosis */}
        <span class="absolute inset-0 opacity-100 animate-shimmer magic-sparkle-shimmer-overlay" />
      </span>
    </Button>
  )
}
