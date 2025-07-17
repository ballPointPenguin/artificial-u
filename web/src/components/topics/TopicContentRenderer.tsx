import { For, Show } from 'solid-js'
import type { TopicContent } from '../../api/types.js'

interface TopicContentRendererProps {
  content: TopicContent
  class?: string
}

export function TopicContentRenderer(props: TopicContentRendererProps) {
  return (
    <Show when={props.content}>
      <div class={`space-y-4 ${props.class || ''}`}>
        <For each={Object.entries(props.content!)}>
          {([key, value]) => (
            <div>
              <h4 class="font-medium text-mystic-300 capitalize mb-2">{key}</h4>
              {Array.isArray(value) ? (
                <ul class="ml-4 space-y-1">
                  <For each={value}>
                    {(item) => (
                      <li class="text-parchment-300 font-serif">
                        • {item}
                      </li>
                    )}
                  </For>
                </ul>
              ) : (
                <p class="text-parchment-300 font-serif">{value}</p>
              )}
            </div>
          )}
        </For>
      </div>
    </Show>
  )
}