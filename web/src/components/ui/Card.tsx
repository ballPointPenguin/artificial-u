import { type JSX, splitProps } from 'solid-js'

interface CardProps {
  class?: string
  children: JSX.Element
  hover?: boolean
  bordered?: boolean
}

export function Card(props: CardProps) {
  const [local, others] = splitProps(props, ['class', 'children', 'hover', 'bordered'])

  return (
    <div
      class={[
        'bg-surface rounded-sm overflow-hidden',
        local.bordered ? 'border border-border/30' : '',
        local.hover ? 'transition-all duration-300 hover:shadow-arcane' : '',
        local.class || '',
      ].join(' ')}
      {...others}
    >
      {local.children}
    </div>
  )
}

export function CardHeader(props: { class?: string; children: JSX.Element }) {
  return <div class={`p-4 border-b border-border/30 ${props.class || ''}`}>{props.children}</div>
}

export function CardContent(props: { class?: string; children: JSX.Element }) {
  return <div class={`p-4 ${props.class || ''}`}>{props.children}</div>
}

export function CardFooter(props: { class?: string; children: JSX.Element }) {
  return <div class={`p-4 border-t border-border/30 ${props.class || ''}`}>{props.children}</div>
}
