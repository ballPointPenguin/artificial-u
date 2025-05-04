import { For, Show, createEffect, createResource } from 'solid-js'
import { getProfessors } from '../../api/services/professor-service'
import type { Professor } from '../../api/types'
import ProfessorListItem from '../professors/ProfessorListItem'

export default function ProfessorList() {
  // Use createResource properly without source signal
  const [professorsResource, { refetch }] = createResource(() => getProfessors({}))

  // Add debug logging
  createEffect(() => {
    console.log('Loading:', professorsResource.loading)
    console.log('Error:', professorsResource.error)
    console.log('Data:', professorsResource())
  })

  // Function to handle retry that returns void
  const handleRetry = () => {
    void refetch()
  }

  return (
    <div>
      <Show
        when={!professorsResource.loading}
        fallback={<p class="text-parchment-300 text-center py-8">Loading professors...</p>}
      >
        <Show
          when={!professorsResource.error}
          fallback={
            <div class="text-red-400 text-center py-8">
              <p>
                Error loading professors:{' '}
                {professorsResource.error instanceof Error
                  ? professorsResource.error.message
                  : 'Unknown error'}
              </p>
              <button
                type="button"
                class="mt-4 px-4 py-2 bg-mystic-800 text-parchment-100 rounded"
                onClick={handleRetry}
              >
                Retry
              </button>
            </div>
          }
        >
          <Show
            when={professorsResource()}
            keyed
            fallback={
              <p class="text-parchment-300 text-center py-8">Could not load professor data.</p>
            }
          >
            {(data) => (
              <Show
                when={data.items.length > 0}
                fallback={<p class="text-parchment-300 text-center py-8">No professors found.</p>}
              >
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <For each={data.items}>
                    {(professor: Professor) => <ProfessorListItem professor={professor} />}
                  </For>
                </div>
                {/* TODO: Add pagination controls using data */}
              </Show>
            )}
          </Show>
        </Show>
      </Show>
    </div>
  )
}
