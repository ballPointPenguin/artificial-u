import { useParams } from '@solidjs/router'
import { Show, createResource } from 'solid-js'
import { getProfessor } from '../../api/services/professor-service'
import type { Professor } from '../../api/types'

export default function ProfessorDetail() {
  const params = useParams()

  // Fetch the specific professor using createResource
  const [professorResource] = createResource(
    () => params.id,
    async (id: string): Promise<Professor> => {
      if (!id) throw new Error('Professor ID is missing')
      // Ensure ID is a number for the API call
      return await getProfessor(Number(id))
    }
  )

  // Type-safe helper to get error message
  const getErrorMessage = () => {
    const error: unknown = professorResource.error
    return error instanceof Error ? error.message : 'Unknown error'
  }

  return (
    <div class="arcane-card p-8">
      {/* Use resource loading state */}
      <Show when={professorResource.loading}>
        <p class="text-parchment-300">Loading professor details...</p>
      </Show>
      {/* Use resource error state */}
      <Show when={professorResource.error !== undefined}>
        <p class="text-red-400">Error loading professor: {getErrorMessage()}</p>
      </Show>
      {/* Use resource data */}
      <Show when={professorResource()} keyed>
        {(prof) => (
          <>
            <h1 class="text-3xl font-display text-parchment-100 mb-4 text-shadow-golden">
              {prof.name}
            </h1>
            <div class="space-y-3 text-parchment-200">
              <p>
                <strong class="font-semibold text-parchment-100">
                  Department:
                </strong>{' '}
                <span class="text-mystic-300">{prof.department}</span>
              </p>
              <p>
                <strong class="font-semibold text-parchment-100">Title:</strong>{' '}
                <span class="text-parchment-200">{prof.title}</span>
              </p>
              <p>
                <strong class="font-semibold text-parchment-100">
                  Specialization:
                </strong>{' '}
                <span class="text-parchment-200">{prof.specialization}</span>
              </p>

              <Show when={prof.description}>
                <p>
                  <strong class="font-semibold text-parchment-100">
                    Description:
                  </strong>
                  <span class="block mt-1 whitespace-pre-wrap">
                    {prof.description}
                  </span>
                </p>
              </Show>

              <Show when={prof.background}>
                <p>
                  <strong class="font-semibold text-parchment-100">
                    Background:
                  </strong>
                  <span class="block mt-1 whitespace-pre-wrap">
                    {prof.background}
                  </span>
                </p>
              </Show>

              <Show when={prof.teaching_style}>
                <p>
                  <strong class="font-semibold text-parchment-100">
                    Teaching Style:
                  </strong>{' '}
                  <span class="text-parchment-200">{prof.teaching_style}</span>
                </p>
              </Show>

              <Show when={prof.personality}>
                <p>
                  <strong class="font-semibold text-parchment-100">
                    Personality:
                  </strong>{' '}
                  <span class="text-parchment-200">{prof.personality}</span>
                </p>
              </Show>

              <Show when={prof.email}>
                <p>
                  <strong class="font-semibold text-parchment-100">
                    Email:
                  </strong>{' '}
                  <a
                    href={prof.email ? `mailto:${prof.email}` : '#'}
                    class="text-vaporwave-400 hover:text-vaporwave-300"
                  >
                    {prof.email}
                  </a>
                </p>
              </Show>

              <Show when={prof.bio}>
                <p>
                  <strong class="font-semibold text-parchment-100">Bio:</strong>
                  <span class="block mt-1 whitespace-pre-wrap">{prof.bio}</span>
                </p>
              </Show>

              {/* Display image if available */}
              <Show when={prof.image_path || prof.image_url}>
                <img
                  src={prof.image_path || prof.image_url || ''}
                  alt={`Professor ${prof.name}`}
                  class="mt-4 max-w-full h-auto rounded-lg shadow-lg"
                />
              </Show>
            </div>
          </>
        )}
      </Show>
    </div>
  )
}
