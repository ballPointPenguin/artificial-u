import { A } from '@solidjs/router'
import { For, Show, createResource, createSignal } from 'solid-js'
import {
  createDepartment,
  getDepartments,
} from '../api/services/department-service'
import type { Department } from '../api/types'
import DepartmentForm from '../components/DepartmentForm'
import { Button } from '../components/ui/Button'

const DepartmentCard = (props: { department: Department }) => {
  return (
    <div class="arcane-card h-full flex flex-col">
      <h3 class="text-xl font-semibold mb-2 text-parchment-100">
        {props.department.name}
      </h3>
      <p class="text-parchment-300 mb-4 line-clamp-3 flex-grow">
        {props.department.description}
      </p>
      <A
        href={`/academics/departments/${String(props.department.id)}`}
        class="text-mystic-500 hover:text-mystic-300 font-medium mt-auto"
      >
        View Details
      </A>
    </div>
  )
}

const DepartmentsPage = () => {
  const [searchQuery, setSearchQuery] = createSignal('')
  const [page, setPage] = createSignal(1)
  const [showCreateForm, setShowCreateForm] = createSignal(false)
  const [submitting, setSubmitting] = createSignal(false)
  const [formError, setFormError] = createSignal('')

  const [departments, { refetch }] = createResource(
    () => ({
      page: page(),
      size: 20,
      name: searchQuery() || undefined,
    }),
    getDepartments
  )

  const handleSearch = (e: Event) => {
    e.preventDefault()
    void refetch()
  }

  const handleSubmitCreate = async (formData: FormData) => {
    setSubmitting(true)
    setFormError('')

    try {
      const newDepartment = {
        name: formData.get('name') as string,
        code: formData.get('code') as string,
        faculty: formData.get('faculty') as string,
        description: formData.get('description') as string,
      }

      await createDepartment(newDepartment)
      setShowCreateForm(false)
      void refetch()
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : 'Failed to create department'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div class="container mx-auto px-4 py-8">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-parchment-100">Departments</h1>
        <Button variant="primary" onClick={() => setShowCreateForm(true)}>
          Add Department
        </Button>
      </div>

      <Show when={showCreateForm()}>
        <div class="arcane-card p-6 mb-8">
          <h2 class="text-xl font-semibold mb-4 text-parchment-100">
            Create New Department
          </h2>
          <DepartmentForm
            onSubmit={(formData) => void handleSubmitCreate(formData)}
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
            placeholder="Search departments..."
            class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-mystic-500 bg-arcanum-800 border-parchment-700/30 text-parchment-100 placeholder:text-parchment-500"
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </div>
      </form>

      {/* Loading and error states */}
      <Show
        when={!departments.loading}
        fallback={<div class="text-center py-8">Loading departments...</div>}
      >
        <Show
          when={!departments.error}
          fallback={
            <div class="text-red-500">
              Error loading departments:{' '}
              {(departments.error as Error).message || 'Unknown error'}
            </div>
          }
        >
          <Show
            when={departments()?.items.length}
            fallback={<div class="text-center py-8">No departments found</div>}
          >
            {/* Departments grid */}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <For each={departments()?.items}>
                {(department) => <DepartmentCard department={department} />}
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
                Page {page()} of {departments()?.pages || 1}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={page() >= (departments()?.pages || 1)}
              >
                Next
              </Button>
            </div>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default DepartmentsPage
