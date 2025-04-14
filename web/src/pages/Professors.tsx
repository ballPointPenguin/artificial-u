import { For, Show, createResource, createSignal } from 'solid-js'
import {
  createProfessor,
  getProfessors,
} from '../api/services/professor-service'
import type { Professor } from '../api/types'
import ProfessorForm, {
  type ProfessorFormData,
} from '../components/professors/ProfessorForm'
import ProfessorListItem from '../components/professors/ProfessorListItem'
import { Button } from '../components/ui/Button'

export default function ProfessorsPage() {
  const [searchQuery, setSearchQuery] = createSignal('')
  const [page, setPage] = createSignal(1)
  const [showCreateForm, setShowCreateForm] = createSignal(false)
  const [submitting, setSubmitting] = createSignal(false)
  const [formError, setFormError] = createSignal('')

  // Fetch professors with search and pagination
  const [professorsResource, { refetch }] = createResource(
    () => ({
      page: page(),
      size: 20,
      name: searchQuery() || undefined,
    }),
    getProfessors
  )

  const handleSearch = (e: Event) => {
    e.preventDefault()
    void refetch()
  }

  const handleSubmitCreate = async (formData: ProfessorFormData) => {
    setSubmitting(true)
    setFormError('')

    try {
      const newProfessor = {
        ...formData,
        specialization: formData.specialization || '',
        background: formData.background || '',
        personality: formData.personality || '',
        image_url: formData.image_url || '',
      }

      await createProfessor(newProfessor)
      setShowCreateForm(false)
      void refetch()
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : 'Failed to create professor'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main class="container mx-auto p-4">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-display mb-6 text-parchment-100 text-shadow-golden">
          Professors
        </h1>
        <Button variant="primary" onClick={() => setShowCreateForm(true)}>
          Add Professor
        </Button>
      </div>

      <Show when={showCreateForm()}>
        <div class="arcane-card p-6 mb-8">
          <h2 class="text-xl font-semibold mb-4 text-parchment-100">
            Create New Professor
          </h2>
          <ProfessorForm
            onSubmit={handleSubmitCreate}
            onCancel={() => setShowCreateForm(false)}
            isSubmitting={submitting()}
            error={formError()}
          />
        </div>
      </Show>

      <form onSubmit={handleSearch} class="mb-8">
        <div class="flex gap-2">
          <input
            type="text"
            value={searchQuery()}
            onInput={(e) => setSearchQuery(e.target.value)}
            placeholder="Search professors..."
            class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-mystic-500 bg-arcanum-800 border-parchment-700/30 text-parchment-100 placeholder:text-parchment-500"
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </div>
      </form>

      {/* Professors List */}
      <Show
        when={!professorsResource.loading}
        fallback={
          <p class="text-parchment-300 text-center py-8">
            Loading professors...
          </p>
        }
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
              <Button
                variant="ghost"
                onClick={() => void refetch()}
                class="mt-4"
              >
                Retry
              </Button>
            </div>
          }
        >
          <Show
            when={professorsResource()?.items.length}
            fallback={<div class="text-center py-8">No professors found</div>}
          >
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <For each={professorsResource()?.items}>
                {(professor: Professor) => (
                  <ProfessorListItem professor={professor} />
                )}
              </For>
            </div>

            {/* Pagination */}
            <div class="mt-8 flex justify-center gap-2">
              <Button
                variant="outline"
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page() <= 1}
              >
                Previous
              </Button>
              <span class="px-4 py-2 flex items-center text-parchment-300">
                Page {page()} of {professorsResource()?.pages || 1}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={page() >= (professorsResource()?.pages || 1)}
              >
                Next
              </Button>
            </div>
          </Show>
        </Show>
      </Show>
    </main>
  )
}
