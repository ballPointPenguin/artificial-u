import { A } from '@solidjs/router'
import { Show } from 'solid-js'
import type { Professor } from '../../api/types'

interface ProfessorListItemProps {
  professor: Professor
}

export default function ProfessorListItem(props: ProfessorListItemProps) {
  return (
    // Ensure ID is converted to string for the URL
    <A
      href={`/professors/${String(props.professor.id)}`}
      class="block arcane-card hover:shadow-glow p-4"
    >
      <div class="flex items-start gap-4">
        <Show when={props.professor.image_url}>
          {(imageUrl) => (
            <img
              src={imageUrl()}
              alt={`Image of ${props.professor.name}`}
              class="w-20 h-20 object-cover rounded-md border border-parchment-500/20"
            />
          )}
        </Show>
        <div class="flex-1">
          <h3 class="text-xl font-display text-parchment-100 mb-1 text-shadow-golden">
            {props.professor.name}
          </h3>
          <p class="text-sm text-parchment-300">
            Title: <span class="text-mystic-300">{props.professor.title}</span>
          </p>
          <p class="text-sm text-parchment-300">
            Specialization: <span class="text-mystic-300">{props.professor.specialization}</span>
          </p>
        </div>
      </div>
    </A>
  )
}
