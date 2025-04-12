import { type JSX, splitProps } from 'solid-js'

type BadgeVariant = 'default' | 'outline' | 'secondary' | 'success' | 'danger'

interface BadgeProps {
  variant?: BadgeVariant
  class?: string
  children: JSX.Element
}

export function Badge(props: BadgeProps) {
  const [local, others] = splitProps(props, ['variant', 'class', 'children'])

  const variantClasses = {
    default: 'bg-parchment-800/40 text-parchment-200',
    outline: 'bg-transparent border border-parchment-400 text-parchment-300',
    secondary: 'bg-mystic-900/40 text-mystic-200',
    success: 'bg-green-900/40 text-green-200',
    danger: 'bg-red-900/40 text-red-200',
  }

  return (
    <span
      class={[
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variantClasses[local.variant || 'default'],
        local.class || '',
      ].join(' ')}
      {...others}
    >
      {local.children}
    </span>
  )
}
