import { A } from '@solidjs/router'
import { createEffect, createResource, createSignal, For, Show } from 'solid-js'
import { departmentService } from '../api/services/department-service.js'
import { facultyService } from '../api/services/faculty-service.js'
import type { Department, Faculty } from '../api/types.js'

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

const FacultyCard = (props: {
  faculty: Faculty
  isSelected: boolean
  onClick: () => void
}) => {
  return (
    <button
      type="button"
      onClick={() => {
        props.onClick()
      }}
      class={`
        arcane-card p-6 text-center transition-all duration-300 cursor-pointer
        min-w-[280px] max-w-xs
        ${props.isSelected
          ? 'border-primary border-2 shadow-arcane bg-surface/80'
          : 'border-border/30 hover:shadow-arcane hover:border-primary/50'
        }
      `}
    >
      <h3 class="text-2xl font-semibold mb-2 text-parchment-100 transition-colors duration-300">
        {props.faculty.name}
      </h3>
    </button>
  )
}

const AcademicsPage = () => {
  const [selectedFacultyId, setSelectedFacultyId] = createSignal<number | null>(null)

  // Fetch all faculties
  const [faculties] = createResource(() => facultyService.listFaculties())

  // Set first faculty as selected by default when faculties load
  createEffect(() => {
    const facs = faculties()
    if (facs && facs.items.length > 0 && selectedFacultyId() === null) {
      setSelectedFacultyId(facs.items[0].id)
    }
  })

  // Fetch departments filtered by selected faculty
  const [departments] = createResource(
    () => {
      const facultyId = selectedFacultyId()
      if (!facultyId) return null
      return {
        page: 1,
        size: 100, // Get all departments for the faculty
        faculty_id: facultyId,
      }
    },
    async (params) => {
      return departmentService.listDepartments(params)
    }
  )

  // Get selected faculty object
  const selectedFaculty = (): Faculty | null => {
    const facs = faculties()
    const id = selectedFacultyId()
    if (!facs || !id) return null
    return facs.items.find((f) => f.id === id) || null
  }

  return (
    <div class="container mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold text-parchment-100 mb-8">Academics</h1>

      {/* Loading faculties */}
      <Show
        when={!faculties.loading}
        fallback={<div class="text-center py-8 text-parchment-300">Loading faculties...</div>}
      >
        <Show
          when={!faculties.error}
          fallback={
            <div class="text-red-500 mb-8">
              Error loading faculties: {(faculties.error as Error).message || 'Unknown error'}
            </div>
          }
        >
          <Show
            when={faculties()?.items && (faculties()?.items.length ?? 0) > 0}
            fallback={<div class="text-center py-8 text-parchment-300">No faculties found</div>}
          >
            {/* Faculty cards menu */}
            <div class="mb-8">
              <h2 class="text-xl font-semibold mb-4 text-parchment-200">Faculties</h2>
              <div class="flex flex-wrap justify-center gap-4">
                <For each={faculties()?.items}>
                  {(faculty) => (
                    <FacultyCard
                      faculty={faculty}
                      isSelected={selectedFacultyId() === faculty.id}
                      onClick={() => setSelectedFacultyId(faculty.id)}
                    />
                  )}
                </For>
              </div>
            </div>

            {/* See all departments link */}
            <div class="mb-8 text-center">
              <A
                href="/departments"
                class="text-parchment-200 hover:text-parchment-100 text-lg tracking-wide transition-colors duration-300 underline underline-offset-4"
              >
                see all departments
              </A>
            </div>

            {/* Selected faculty description */}
            <Show when={selectedFaculty()}>
              {(faculty) => (
                <div class="mb-8">
                  <div class="arcane-card p-6">
                    <h2 class="text-2xl font-semibold mb-4 text-parchment-100">
                      {faculty().name}
                    </h2>
                    <Show
                      when={faculty().description}
                      fallback={
                        <p class="text-parchment-300 italic">No description available.</p>
                      }
                    >
                      <p class="text-parchment-200 whitespace-pre-line text-lg">
                        {faculty().description}
                      </p>
                    </Show>
                  </div>
                </div>
              )}
            </Show>

            {/* Departments for selected faculty */}
            <div class="mb-6">
              <h2 class="text-xl font-semibold mb-4 text-parchment-200">Departments</h2>
              <Show
                when={!departments.loading}
                fallback={
                  <div class="text-center py-8 text-parchment-300">Loading departments...</div>
                }
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
                    fallback={
                      <div class="text-center py-8 text-parchment-300">
                        No departments found for this faculty.
                      </div>
                    }
                  >
                    {/* Departments grid */}
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      <For each={departments()?.items}>
                        {(department) => <DepartmentCard department={department} />}
                      </For>
                    </div>
                  </Show>
                </Show>
              </Show>
            </div>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default AcademicsPage

