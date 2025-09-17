import { Button as KobalteButton } from '@kobalte/core/button'
import { type JSX, splitProps } from 'solid-js'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends JSX.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: JSX.Element
}

export function Button(props: ButtonProps) {
  const [local, others] = splitProps(props, ['variant', 'size', 'class', 'children', 'disabled'])

  // Base classes for all buttons - removed cursor-pointer to avoid conflict
  const baseClasses =
    'rounded font-serif tracking-wider transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary'

  // Make stateClasses a getter function for reactive updates
  const stateClasses = () =>
    local.disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : 'cursor-pointer'

  const variantClasses = {
    primary:
      // Using text-foreground for better contrast on vibrant primary backgrounds across themes.
      'bg-primary text-foreground border border-accent/70 shadow-arcane enabled:hover:shadow-glow',
    secondary: 'bg-surface enabled:hover:bg-surface/80 text-foreground border border-border',
    outline: 'bg-transparent text-primary border border-primary enabled:hover:bg-primary/10',
    ghost: 'bg-transparent text-muted enabled:hover:text-primary enabled:hover:bg-primary/10',
    link: 'bg-transparent text-primary underline-offset-4 enabled:hover:underline',
    danger:
      'bg-danger-bg border border-danger-border text-danger enabled:hover:bg-danger enabled:hover:text-foreground',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <KobalteButton
      class={[
        baseClasses,
        stateClasses(),
        variantClasses[local.variant || 'primary'],
        sizeClasses[local.size || 'md'],
        local.class || '',
      ].join(' ')}
      disabled={local.disabled}
      {...others}
    >
      {local.children}
    </KobalteButton>
  )
}
