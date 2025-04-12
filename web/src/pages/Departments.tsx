import { A } from '@solidjs/router'
import { For, Show, createResource, createSignal } from 'solid-js'
import { getDepartments } from '../api/services/department-service'
import type { Department } from '../api/types'

const DepartmentCard = (props: { department: Department }) => {
  return (
    <div class="bg-white shadow rounded-lg p-4 hover:shadow-md transition-shadow">
      <h3 class="text-xl font-semibold mb-2">{props.department.name}</h3>
      <p class="text-gray-600 mb-4 line-clamp-3">
        {props.department.description}
      </p>
      <A
        href={`/departments/${String(props.department.id)}`}
        class="text-blue-600 hover:text-blue-800 font-medium"
      >
        View Details
      </A>
    </div>
  )
}

const DepartmentsPage = () => {
  const [searchQuery, setSearchQuery] = createSignal('')
  const [page, setPage] = createSignal(1)

  // Create a resource to fetch departments
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

  return (
    <div class="container mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold mb-6">Departments</h1>

      {/* Search form */}
      <form onSubmit={handleSearch} class="mb-8">
        <div class="flex gap-2">
          <input
            type="text"
            value={searchQuery()}
            onInput={(e) => setSearchQuery(e.target.value)}
            placeholder="Search departments..."
            class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Search
          </button>
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
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page() <= 1}
                class="px-4 py-2 rounded bg-gray-200 disabled:opacity-50"
              >
                Previous
              </button>
              <span class="px-4 py-2">
                Page {page()} of {departments()?.pages || 1}
              </span>
              <button
                type="button"
                onClick={() => setPage((p) => p + 1)}
                disabled={page() >= (departments()?.pages || 1)}
                class="px-4 py-2 rounded bg-gray-200 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default DepartmentsPage
