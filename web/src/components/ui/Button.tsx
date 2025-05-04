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

  const variantClasses = {
    primary:
      'bg-gradient-to-r from-parchment-700/50 to-mystic-800/50 text-parchment-100 border border-parchment-500/50 shadow-arcane hover:shadow-glow',
    secondary:
      'bg-arcanum-900/50 hover:bg-arcanum-800/50 text-parchment-200 border border-parchment-400',
    outline:
      'bg-transparent text-parchment-200 border border-parchment-400 hover:bg-parchment-800/20',
    ghost: 'bg-transparent text-parchment-300 hover:text-parchment-100 hover:bg-arcanum-800/30',
    link: 'bg-transparent text-parchment-200 hover:text-parchment-100 underline-offset-4 hover:underline',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <KobalteButton
      class={[
        'rounded font-serif tracking-wider transition-all duration-300',
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
