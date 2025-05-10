import * as KobalteTooltip from '@kobalte/core/tooltip'
import type { JSX } from 'solid-js'

interface TooltipProps {
  content: JSX.Element
  children: JSX.Element
  side?: 'top' | 'right' | 'bottom' | 'left'
}

export function Tooltip(props: TooltipProps) {
  return (
    <KobalteTooltip.Root placement={props.side || 'top'}>
      <KobalteTooltip.Trigger>{props.children}</KobalteTooltip.Trigger>
      <KobalteTooltip.Portal>
        <KobalteTooltip.Content
          class="z-50 p-2 rounded shadow-arcane max-w-xs text-sm
                 bg-surface/95 border border-border text-foreground"
        >
          {props.content}
          <KobalteTooltip.Arrow />
        </KobalteTooltip.Content>
      </KobalteTooltip.Portal>
    </KobalteTooltip.Root>
  )
}
