import { A } from '@solidjs/router'
import { createResource, createSignal, For, Show } from 'solid-js'
import { departmentService } from '../api/services/department-service.js'
import { facultyService } from '../api/services/faculty-service.js'
import type { Department, DepartmentCreate } from '../api/types.js'
import { RequireRole } from '../auth/RequireRole'
import DepartmentForm from '../components/departments/DepartmentForm.js'
import { Button, Input, Select, type SelectOption } from '../components/ui'

const DepartmentCard = (props: { department: Department }) => {
  return (
    <A
      href={`/departments/${String(props.department.id)}`}
      class="arcane-card h-full flex flex-col hover:shadow-arcane hover:scale-105 hover:border-primary/50 transition-all duration-300 cursor-pointer group"
    >
      <h3 class="text-xl font-semibold mb-2 text-parchment-100 group-hover:text-primary transition-colors duration-300">
        {props.department.name}
      </h3>
      <p class="text-parchment-300 mb-4 line-clamp-3 flex-grow group-hover:text-parchment-200 transition-colors duration-300">
        {props.department.description}
      </p>
    </A>
  )
}

const DepartmentsPage = () => {
  const [searchQuery, setSearchQuery] = createSignal('')
  const [selectedFacultyId, setSelectedFacultyId] = createSignal<number | null>(null)
  const [page, setPage] = createSignal(1)
  const [showCreateForm, setShowCreateForm] = createSignal(false)
  const [submitting, setSubmitting] = createSignal(false)
  const [formError, setFormError] = createSignal('')

  // Fetch all faculties
  const [faculties] = createResource(() => facultyService.listFaculties())

  // Create faculty options for the dropdown
  const facultyOptions = (): SelectOption[] => {
    const facs = faculties()
    if (!facs) return []
    return [
      { value: 'all', label: 'All Faculties' },
      ...facs.items.map((faculty) => ({
        value: faculty.id,
        label: faculty.name,
      })),
    ]
  }

  const [departments, { refetch }] = createResource(() => {
    const facultyId = selectedFacultyId()
    return {
      page: page(),
      size: 20,
      name: searchQuery() || undefined,
      faculty_id: facultyId || undefined,
    }
  }, departmentService.listDepartments)

  const handleSearch = (e: Event) => {
    e.preventDefault()
    setPage(1) // Reset to first page when searching
    void refetch()
  }

  const handleFacultyChange = (value: SelectOption['value'] | null) => {
    if (value === 'all' || value === null) {
      setSelectedFacultyId(null)
    } else {
      setSelectedFacultyId(value as number)
    }
    setPage(1) // Reset to first page when filter changes
    // Resource will automatically refetch when selectedFacultyId or page changes
  }

  const handleSubmitCreate = async (formData: FormData) => {
    setSubmitting(true)
    setFormError('')

    try {
      const facultyIdStr = formData.get('faculty_id') as string | null
      const newDepartment: DepartmentCreate = {
        name: formData.get('name') as string,
        code: formData.get('code') as string,
        faculty_id: facultyIdStr ? Number.parseInt(facultyIdStr, 10) : null,
        description: formData.get('description') as string,
      }

      await departmentService.createDepartment(newDepartment)
      setShowCreateForm(false)
      void refetch()
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Failed to create department')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div class="container mx-auto px-4 py-8">
      <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6">
        <h1 class="text-3xl font-bold text-parchment-100">Departments</h1>
        <RequireRole minRole="creator">
          <Button
            variant="primary"
            onClick={() => setShowCreateForm(true)}
            class="w-full sm:w-auto"
          >
            Add Department
          </Button>
        </RequireRole>
      </div>

      <Show when={showCreateForm()}>
        <RequireRole minRole="creator">
          <div class="arcane-card p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4 text-parchment-100">Create New Department</h2>
            <DepartmentForm
              onSubmit={(formData) => void handleSubmitCreate(formData)}
              onCancel={() => setShowCreateForm(false)}
              isSubmitting={submitting()}
              error={formError()}
            />
          </div>
        </RequireRole>
      </Show>

      <form onSubmit={handleSearch} class="mb-8 space-y-2">
        {/* Search input and button row - always together */}
        <div class="flex gap-2">
          <Input
            name="search"
            type="text"
            value={searchQuery()}
            onInput={(e) => setSearchQuery(e.currentTarget.value)}
            placeholder="Search departments..."
            class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-mystic-500 bg-arcanum-800 border-parchment-700/30 text-parchment-100 placeholder:text-parchment-500"
          />
          <Button type="submit" variant="secondary" class="shrink-0">
            Search
          </Button>
        </div>
        {/* Faculty dropdown - on its own line with responsive width */}
        <Show
          when={!faculties.loading && faculties()?.items}
          fallback={
            <div class="w-full sm:w-auto sm:min-w-64 px-4 py-2 border rounded-lg bg-arcanum-800 border-parchment-700/30 text-parchment-300 flex items-center">
              Loading faculties...
            </div>
          }
        >
          <Select
            name="faculty"
            options={facultyOptions()}
            value={selectedFacultyId() ?? 'all'}
            onChange={handleFacultyChange}
            placeholder="All Faculties"
            class="w-full sm:w-auto sm:min-w-64 sm:max-w-md"
          />
        </Show>
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
              Error loading departments: {(departments.error as Error).message || 'Unknown error'}
            </div>
          }
        >
          <Show
            when={departments()?.items && (departments()?.items.length ?? 0) > 0}
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
