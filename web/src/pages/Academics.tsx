import { A } from '@solidjs/router'
import { createEffect, createResource, createSignal, For, Show } from 'solid-js'
import { departmentService } from '../api/services/department-service.js'
import { facultyService } from '../api/services/faculty-service.js'
import type { Department, Faculty } from '../api/types.js'
import { useContentLanguage, useTranslations } from '../i18n'

const DepartmentCard = (props: { department: Department }) => {
  return (
    <A
      href={`/departments/${String(props.department.id)}`}
      class="arcane-card h-full flex flex-col overflow-hidden hover:shadow-arcane hover:scale-105 hover:border-primary/50 transition-all duration-300 cursor-pointer group"
    >
      <h3 class="text-xl font-semibold mb-2 text-parchment-100 line-clamp-2 shrink-0 group-hover:text-primary transition-colors duration-300">
        {props.department.name}
      </h3>
      <p class="text-sm text-parchment-300 line-clamp-2 min-h-0 group-hover:text-parchment-200 transition-colors duration-300">
        {props.department.description}
      </p>
    </A>
  )
}

const FacultyCard = (props: { faculty: Faculty; isSelected: boolean; onClick: () => void }) => {
  return (
    <button
      type="button"
      onClick={() => {
        props.onClick()
      }}
      class={`
        arcane-card p-2 text-center transition-all duration-300 cursor-pointer
        shrink-0 snap-start min-w-[9rem] max-w-[12rem] md:min-w-[12rem] md:max-w-[16rem] h-20 flex items-center justify-center
        ${
          props.isSelected
            ? 'border-primary border-2 shadow-arcane bg-surface/80'
            : 'border-border/30 hover:shadow-arcane hover:border-primary/50 bg-surface/20'
        }
      `}
    >
      <h3
        class={`
        text-xs md:text-sm font-display tracking-wider leading-tight transition-colors duration-300
        line-clamp-2 whitespace-normal w-full px-1 text-balance
        ${props.isSelected ? 'text-primary' : 'text-parchment-200'}
      `}
      >
        {props.faculty.name}
      </h3>
    </button>
  )
}

const AcademicsPage = () => {
  const t = useTranslations()
  const { contentLanguage } = useContentLanguage()
  const [selectedFacultyId, setSelectedFacultyId] = createSignal<number | null>(null)

  // Fetch all faculties
  const [faculties] = createResource(() =>
    facultyService.listFaculties({ language: contentLanguage() })
  )

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
        language: contentLanguage(),
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
      <h1 class="text-3xl font-bold text-parchment-100 mb-8">{t().academics.title}</h1>

      {/* Loading faculties */}
      <Show
        when={!faculties.loading}
        fallback={
          <div class="text-center py-8 text-parchment-300">{t().academics.loadingFaculties}</div>
        }
      >
        <Show
          when={!faculties.error}
          fallback={
            <div class="text-red-500 mb-8">
              {t().academics.errorLoadingFaculties}:{' '}
              {(faculties.error as Error).message || t().common.unknownError}
            </div>
          }
        >
          <Show
            when={faculties()?.items && (faculties()?.items.length ?? 0) > 0}
            fallback={
              <div class="text-center py-8 text-parchment-300">
                {t().academics.noFacultiesFound}
              </div>
            }
          >
            {/* Faculty cards menu - Carousel */}
            <div class="mb-10">
              <h2 class="text-xs font-display uppercase tracking-[0.2em] mb-4 text-muted/80 px-1">
                {t().academics.faculties}
              </h2>
              <div class="flex overflow-x-auto gap-3 pb-6 -mx-4 px-4 snap-x snap-proximity no-scrollbar scroll-smooth">
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
                {t().academics.seeAllDepartments}
              </A>
            </div>

            <Show when={selectedFaculty()}>
              {(faculty) => (
                <div class="mb-8">
                  <div class="arcane-card p-6">
                    <h2 class="text-xl font-semibold mb-4 text-parchment-100">{faculty().name}</h2>
                    <Show
                      when={faculty().description}
                      fallback={<p class="text-parchment-300 italic">{t().common.noDescription}</p>}
                    >
                      <p class="text-parchment-200 whitespace-pre-line text-base">
                        {faculty().description}
                      </p>
                    </Show>
                  </div>
                </div>
              )}
            </Show>

            {/* Departments for selected faculty */}
            <div class="mb-6">
              <h2 class="text-xl font-semibold mb-4 text-parchment-200">
                {t().academics.departments}
              </h2>
              <Show
                when={!departments.loading}
                fallback={
                  <div class="text-center py-8 text-parchment-300">
                    {t().academics.loadingDepartments}
                  </div>
                }
              >
                <Show
                  when={!departments.error}
                  fallback={
                    <div class="text-red-500">
                      {t().academics.errorLoadingDepartments}:{' '}
                      {(departments.error as Error).message || t().common.unknownError}
                    </div>
                  }
                >
                  <Show
                    when={departments()?.items && (departments()?.items.length ?? 0) > 0}
                    fallback={
                      <div class="text-center py-8 text-parchment-300">
                        {t().academics.noDepartmentsFound}
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
