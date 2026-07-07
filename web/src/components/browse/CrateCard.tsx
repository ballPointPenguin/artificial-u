import { A } from '@solidjs/router'
import { type Component, For, Show } from 'solid-js'
import type { Course } from '../../api/types.js'

interface CrateCardProps {
  course: Course
  class?: string
}

/**
 * A cover-art-forward "record sleeve" card for the Browse page.
 * Generated album art already bakes in the title and professor name, so
 * those are only overlaid as text when there's no art to fall back on.
 */
const CrateCard: Component<CrateCardProps> = (props) => {
  const tags = () => (props.course.tags ?? []).slice(0, 3)

  return (
    <A
      href={`/courses/${String(props.course.id)}`}
      class={`card-hover-lift block overflow-hidden rounded-lg border border-border/30 bg-surface no-underline ${props.class ?? ''}`}
    >
      <div class="relative aspect-square w-full overflow-hidden">
        <Show
          when={props.course.image_url}
          fallback={
            <div class="flex h-full w-full items-center justify-center bg-gradient-to-br from-primary/25 via-surface to-secondary/20">
              <span class="select-none font-display text-4xl tracking-widest text-primary/60">
                {props.course.code}
              </span>
            </div>
          }
        >
          <img
            src={props.course.image_url ?? ''}
            alt={props.course.title}
            loading="lazy"
            class="h-full w-full object-cover"
          />
        </Show>
        <Show when={!props.course.image_url}>
          <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 pt-10">
            <h3 class="line-clamp-2 font-display text-base leading-snug text-white">
              {props.course.title}
            </h3>
            <Show when={props.course.professor?.name}>
              <p class="mt-0.5 font-serif text-xs text-white/70">{props.course.professor?.name}</p>
            </Show>
          </div>
        </Show>
      </div>
      <Show when={tags().length > 0}>
        <div class="flex flex-wrap gap-1.5 p-3">
          <For each={tags()}>
            {(tag) => (
              <span class="tag-teal inline-block rounded px-2 py-0.5 font-sans text-[11px] font-medium">
                {tag.name}
              </span>
            )}
          </For>
        </div>
      </Show>
    </A>
  )
}

export default CrateCard
