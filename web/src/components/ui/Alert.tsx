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
    default: 'bg-arcanum-800/50 border-parchment-700/30 text-parchment-200',
    info: 'bg-vaporwave-900/30 border-vaporwave-700/30 text-vaporwave-200',
    success: 'bg-green-900/30 border-green-700/30 text-green-200',
    warning: 'bg-amber-900/30 border-amber-700/30 text-amber-200',
    danger: 'bg-red-900/30 border-red-700/30 text-red-200',
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
      <div class="flex">
        <Show when={local.icon}>
          <div class="flex-shrink-0 mr-3">{local.icon}</div>
        </Show>

        <div>
          <Show when={local.title}>
            <h3 class="text-lg font-serif mb-1">{local.title}</h3>
          </Show>

          <div class="text-sm font-serif">{local.children}</div>
        </div>
      </div>
    </div>
  )
}
