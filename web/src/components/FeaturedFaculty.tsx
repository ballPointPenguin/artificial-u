import * as Tooltip from '@kobalte/core/tooltip'
import { type Component, For } from 'solid-js'

interface FacultyMember {
  id: string
  name: string
  title: string
  shortName?: string
  imageUrl: string
  specialty?: string
}

interface FeaturedFacultyProps {
  title?: string
  faculty: FacultyMember[]
}

// New Sub-component for individual faculty member
const FacultyMemberCard: Component<{ member: FacultyMember }> = (props) => {
  const { member } = props
  return (
    <div class="group">
      <Tooltip.Root>
        <Tooltip.Trigger class="block w-full">
          <div class="aspect-w-1 aspect-h-1 overflow-hidden rounded bg-surface">
            <div class="relative w-full h-full">
              <img
                src={member.imageUrl}
                alt={member.name}
                class="w-full h-full object-cover transition-all duration-500 group-hover:scale-105"
              />
              <div class="absolute inset-0 bg-gradient-to-t from-background/90 via-background/20 to-transparent opacity-90" />
            </div>
          </div>

          <div class="text-center mt-6 space-y-2">
            <h3 class="text-xl font-display text-foreground group-hover:text-primary transition-colors">
              {member.name}
            </h3>
            <p class="text-muted font-serif italic">
              {member.shortName || member.name.split(' ')[0]}
            </p>
          </div>
        </Tooltip.Trigger>

        <Tooltip.Portal>
          <Tooltip.Content class="z-50 p-3 bg-surface/95 border border-border text-foreground rounded shadow-arcane max-w-xs">
            <div class="space-y-2">
              <p class="font-display text-primary">{member.name}</p>
              <p class="font-serif text-sm">{member.title}</p>
              {member.specialty && (
                <p class="text-xs italic text-muted/80">Specialty: {member.specialty}</p>
              )}
            </div>
            <Tooltip.Arrow />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </div>
  )
}

export function FeaturedFaculty(props: FeaturedFacultyProps) {
  return (
    <section class="py-20 bg-background relative overflow-hidden">
      <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-4xl font-display text-primary text-center mb-16 text-shadow-golden">
          {props.title}
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
          <For each={props.faculty}>{(member) => <FacultyMemberCard member={member} />}</For>
        </div>
      </div>
    </section>
  )
}
