import { type JSX } from '@solidjs/web'
import { omit, Show } from 'solid-js'

type AlertVariant = 'default' | 'info' | 'success' | 'warning' | 'danger'

interface AlertProps {
  variant?: AlertVariant
  title?: string
  class?: string
  children: JSX.Element
  icon?: JSX.Element
}

export function Alert(props: AlertProps) {
  const others = omit(props, 'variant', 'title', 'class', 'children', 'icon')

  const variantClasses = {
    default: 'bg-surface/80 border-border text-muted',
    info: 'bg-info-bg border-info-border text-info',
    success: 'bg-success-bg border-success-border text-success',
    warning: 'bg-warning-bg border-warning-border text-warning',
    danger: 'bg-danger-bg border-danger-border text-danger',
  }

  return (
    <div
      class={[
        'p-4 rounded-sm border',
        variantClasses[props.variant || 'default'],
        props.class || '',
      ].join(' ')}
      role="alert"
      {...others}
    >
      <div class="flex items-start">
        <Show when={props.icon}>
          <div
            class={`flex-shrink-0 mr-3 ${variantClasses[props.variant || 'default'].split(' ').find((cls) => cls.startsWith('text-')) || 'text-muted'}`}
          >
            {props.icon}
          </div>
        </Show>

        <div>
          <Show when={props.title}>
            <h3 class="text-lg font-serif mb-1 font-medium text-foreground">{props.title}</h3>
          </Show>

          <div class="text-sm font-serif">{props.children}</div>
        </div>
      </div>
    </div>
  )
}
