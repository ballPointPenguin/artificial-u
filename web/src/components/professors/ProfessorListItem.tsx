import { A } from '@solidjs/router'
import type { Professor } from '../../api/types'

interface ProfessorListItemProps {
  professor: Professor
}

export default function ProfessorListItem(props: ProfessorListItemProps) {
  return (
    // Ensure ID is converted to string for the URL
    <A
      href={`/professors/${String(props.professor.id)}`}
      class="block arcane-card hover:shadow-glow"
    >
      <h3 class="text-xl font-display text-parchment-100 mb-2 text-shadow-golden">
        {props.professor.name}
      </h3>
      <p class="text-sm text-parchment-300">
        Title: <span class="text-mystic-300">{props.professor.title}</span>
      </p>
      <p class="text-sm text-parchment-300">
        Specialization: <span class="text-mystic-300">{props.professor.specialization}</span>
      </p>
    </A>
  )
}
