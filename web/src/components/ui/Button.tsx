import { Button as KobalteButton } from '@kobalte/core/button'
import { type JSX } from '@solidjs/web'
import { omit } from 'solid-js'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends JSX.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: JSX.Element
}

export function Button(props: ButtonProps) {
  const others = omit(props, 'variant', 'size', 'class', 'children', 'disabled')

  // Base classes for all buttons - removed cursor-pointer to avoid conflict
  const baseClasses =
    'rounded font-serif tracking-wider transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary'

  // Make stateClasses a getter function for reactive updates
  const stateClasses = () =>
    props.disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : 'cursor-pointer'

  const variantClasses = {
    primary:
      'bg-primary text-on-primary border border-accent/70 shadow-arcane enabled:hover:shadow-glow',
    secondary: 'bg-surface enabled:hover:bg-surface/80 text-foreground border border-border',
    outline: 'bg-transparent text-primary border border-primary enabled:hover:bg-primary/10',
    ghost:
      'bg-transparent text-foreground/70 enabled:hover:text-foreground enabled:hover:bg-primary/10',
    link: 'bg-transparent text-primary underline-offset-4 enabled:hover:underline',
    danger:
      'bg-danger-bg border border-danger-border text-danger enabled:hover:bg-danger enabled:hover:text-foreground',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  }

  const className = () =>
    [
      baseClasses,
      stateClasses(),
      variantClasses[props.variant || 'primary'],
      sizeClasses[props.size || 'md'],
      typeof props.class === 'string' ? props.class : '',
    ]
      .filter((part) => part.length > 0)
      .join(' ')

  return (
    <KobalteButton class={className()} disabled={Boolean(props.disabled)} {...(others as object)}>
      {props.children}
    </KobalteButton>
  )
}
