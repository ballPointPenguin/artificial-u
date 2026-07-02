import { A } from '@solidjs/router'
import { X } from 'lucide-solid'
import { type Component, Show } from 'solid-js'
import type { Tag } from '../../api/types.js'

interface TagChipProps {
  tag: Tag
  /** Link the chip to the Browse page filtered by this tag */
  link?: boolean
  /** Show a remove button and call back when clicked */
  onRemove?: (tag: Tag) => void
  class?: string
}

const PILL_CLASS =
  'tag-teal inline-flex items-center gap-1 rounded px-2.5 py-0.5 text-xs font-sans font-medium'

const TagChip: Component<TagChipProps> = (props) => {
  return (
    <Show
      when={props.link}
      fallback={
        <span class={`${PILL_CLASS} ${props.class ?? ''}`}>
          {props.tag.name}
          <Show when={props.onRemove}>
            <button
              type="button"
              class="cursor-pointer opacity-70 hover:opacity-100 transition-opacity"
              aria-label={`Remove ${props.tag.name}`}
              onClick={() => props.onRemove?.(props.tag)}
            >
              <X size={12} />
            </button>
          </Show>
        </span>
      }
    >
      <A
        href={`/browse?tags=${encodeURIComponent(props.tag.slug)}`}
        class={`${PILL_CLASS} hover:opacity-80 transition-opacity ${props.class ?? ''}`}
      >
        {props.tag.name}
      </A>
    </Show>
  )
}

export default TagChip
