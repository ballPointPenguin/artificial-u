import { A } from '@solidjs/router'
import { Show } from 'solid-js'
import type { Professor } from '../../api/types'

interface ProfessorListItemProps {
  professor: Professor
}

export default function ProfessorListItem(props: ProfessorListItemProps) {
  return (
    <A
      href={`/professors/${String(props.professor.id)}`}
      class="arcane-card group flex h-full flex-col p-4 transition-all duration-300 hover:border-primary/30 hover:shadow-glow"
    >
      <div class="flex flex-col items-center text-center">
        <Show when={props.professor.image_url}>
          {(imageUrl) => (
            <div class="flex-shrink-0">
              <img
                src={imageUrl()}
                alt={props.professor.name}
                class="mb-4 h-32 w-32 rounded-full border-2 border-parchment-500/10 object-cover shadow-lg transition-all duration-300 group-hover:border-primary/40 group-hover:shadow-golden-glow"
              />
            </div>
          )}
        </Show>
        <div class="flex-1">
          <h3 class="mb-1 font-display text-2xl text-parchment-100 text-shadow-golden transition-colors duration-300 group-hover:text-golden-300">
            {props.professor.name}
          </h3>
          <p class="font-serif text-base italic text-mystic-300/80 transition-colors duration-300 group-hover:text-mystic-300">
            {props.professor.title}
          </p>
          <div class="mt-3 border-t border-parchment-500/10 pt-3">
            <p class="text-sm text-mystic-300/90 line-clamp-3">{props.professor.specialization}</p>
          </div>
        </div>
      </div>
    </A>
  )
}
