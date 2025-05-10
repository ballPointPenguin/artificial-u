import { type JSX, Show, splitProps } from 'solid-js'

type AlertVariant = 'default' | 'info' | 'success' | 'warning' | 'danger'

interface AlertProps {
  variant?: AlertVariant
  title?: string
  class?: string
  children: JSX.Element
  icon?: JSX.Element
}

export function Alert(props: AlertProps) {
  const [local, others] = splitProps(props, ['variant', 'title', 'class', 'children', 'icon'])

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
        variantClasses[local.variant || 'default'],
        local.class || '',
      ].join(' ')}
      role="alert"
      {...others}
    >
      <div class="flex items-start">
        <Show when={local.icon}>
          <div
            class={`flex-shrink-0 mr-3 ${variantClasses[local.variant || 'default'].split(' ').find((cls) => cls.startsWith('text-')) || 'text-muted'}`}
          >
            {local.icon}
          </div>
        </Show>

        <div>
          <Show when={local.title}>
            <h3 class="text-lg font-serif mb-1 font-medium text-foreground">{local.title}</h3>
          </Show>

          <div class="text-sm font-serif">{local.children}</div>
        </div>
      </div>
    </div>
  )
}
