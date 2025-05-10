import { Button as KobalteButton } from '@kobalte/core/button'
import { type JSX, splitProps } from 'solid-js'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'link'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends JSX.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: JSX.Element
}

export function Button(props: ButtonProps) {
  const [local, others] = splitProps(props, ['variant', 'size', 'class', 'children'])

  // Base classes for all buttons
  const baseClasses =
    'rounded font-serif tracking-wider transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary ui-disabled:opacity-50 ui-disabled:cursor-not-allowed cursor-pointer'

  const variantClasses = {
    primary:
      // Using text-foreground for better contrast on vibrant primary backgrounds across themes.
      'bg-primary text-foreground border border-accent/70 shadow-arcane hover:shadow-glow',
    secondary: 'bg-surface hover:bg-surface/80 text-foreground border border-border',
    outline: 'bg-transparent text-primary border border-primary hover:bg-primary/10',
    ghost: 'bg-transparent text-muted hover:text-primary hover:bg-primary/10',
    link: 'bg-transparent text-primary underline-offset-4 hover:underline',
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
        variantClasses[local.variant || 'primary'],
        sizeClasses[local.size || 'md'],
        local.class || '',
      ].join(' ')}
      {...others}
    >
      {local.children}
    </KobalteButton>
  )
}
