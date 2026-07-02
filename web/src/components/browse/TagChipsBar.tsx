import { type Component, For } from 'solid-js'
import type { TagWithCount } from '../../api/types.js'

interface TagChipsBarProps {
  tags: TagWithCount[]
  selected: string[]
  onToggle: (slug: string) => void
  onClear: () => void
  allLabel: string
}

const BASE_CHIP_CLASS =
  'shrink-0 cursor-pointer rounded-full border px-3 py-1 font-sans text-xs font-medium transition-colors'

/**
 * Horizontally scrollable tag filter chips. Selected chips toggle slugs in
 * the page's `?tags=` URL state; the leading "All" chip clears the filter.
 */
const TagChipsBar: Component<TagChipsBarProps> = (props) => {
  const isSelected = (slug: string) => props.selected.includes(slug)

  return (
    <div class="-mx-4 flex gap-2 overflow-x-auto px-4 pb-2">
      <button
        type="button"
        class={`${BASE_CHIP_CLASS} ${
          props.selected.length === 0
            ? 'border-primary bg-primary text-on-primary'
            : 'border-border text-muted hover:border-primary hover:text-primary'
        }`}
        onClick={() => {
          props.onClear()
        }}
      >
        {props.allLabel}
      </button>
      <For each={props.tags}>
        {(tag) => (
          <button
            type="button"
            class={`${BASE_CHIP_CLASS} ${
              isSelected(tag.slug)
                ? 'border-primary bg-primary text-on-primary'
                : 'border-border text-muted hover:border-primary hover:text-primary'
            }`}
            aria-pressed={isSelected(tag.slug)}
            onClick={() => {
              props.onToggle(tag.slug)
            }}
          >
            {tag.name}
          </button>
        )}
      </For>
    </div>
  )
}

export default TagChipsBar
