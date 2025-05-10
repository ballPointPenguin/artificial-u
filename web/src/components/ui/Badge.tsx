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
    default: 'bg-surface text-muted',
    outline: 'bg-transparent border border-border text-muted',
    secondary: 'bg-accent/40 text-accent',
    success: 'bg-success-bg text-success',
    danger: 'bg-danger-bg text-danger',
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
