import { createResource, createSignal, For, Show } from 'solid-js'
import { departmentService } from '../api/services/department-service.js'
import { facultyService } from '../api/services/faculty-service.js'
import { professorService } from '../api/services/professor-service.js'
import type { Professor } from '../api/types.js'
import { RequireRole } from '../auth/RequireRole'
import ProfessorForm, { type ProfessorFormData } from '../components/professors/ProfessorForm.js'
import ProfessorListItem from '../components/professors/ProfessorListItem.js'
import { Button, Input, Select, type SelectOption } from '../components/ui'
import { useTranslations } from '../i18n'

export default function ProfessorsPage() {
  const t = useTranslations()
  const [searchQuery, setSearchQuery] = createSignal('')
  const [selectedFacultyId, setSelectedFacultyId] = createSignal<number | null>(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = createSignal<number | null>(null)
  const [page, setPage] = createSignal(1)
  const [showCreateForm, setShowCreateForm] = createSignal(false)
  const [submitting, setSubmitting] = createSignal(false)
  const [formError, setFormError] = createSignal('')

  // Fetch all faculties
  const [faculties] = createResource(() => facultyService.listFaculties())

  // Fetch departments, filtered by selected faculty if one is selected
  const [departments] = createResource(
    () => ({
      page: 1,
      size: 100, // Get all departments for dropdown
      faculty_id: selectedFacultyId() || undefined,
    }),
    departmentService.listDepartments
  )

  // Create faculty options for the dropdown
  const facultyOptions = (): SelectOption[] => {
    const facs = faculties()
    if (!facs) return []
    return [
      { value: 'all', label: t().professors.allFaculties },
      ...facs.items.map((faculty) => ({
        value: faculty.id,
        label: faculty.name,
      })),
    ]
  }

  // Create department options for the dropdown, filtered by selected faculty
  const departmentOptions = (): SelectOption[] => {
    const depts = departments()
    if (!depts) return []
    return [
      { value: 'all', label: t().professors.allDepartments },
      ...depts.items.map((department) => ({
        value: department.id,
        label: department.name,
      })),
    ]
  }

  // Fetch professors with search and pagination
  const [professorsResource, { refetch }] = createResource(
    () => ({
      page: page(),
      size: 20,
      name: searchQuery() || undefined,
      facultyId: selectedFacultyId() || undefined,
      departmentId: selectedDepartmentId() || undefined,
    }),
    professorService.listProfessors
  )

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
    // Reset department selection when faculty changes
    setSelectedDepartmentId(null)
    setPage(1) // Reset to first page when filter changes
    // Resource will automatically refetch when selectedFacultyId or page changes
  }

  const handleDepartmentChange = (value: SelectOption['value'] | null) => {
    if (value === 'all' || value === null) {
      setSelectedDepartmentId(null)
    } else {
      setSelectedDepartmentId(value as number)
    }
    setPage(1) // Reset to first page when filter changes
    // Resource will automatically refetch when selectedDepartmentId or page changes
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

      await professorService.createProfessor(newProfessor)
      setShowCreateForm(false)
      void refetch()
    } catch (error) {
      setFormError(error instanceof Error ? error.message : t().professors.failedToCreate)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main class="container mx-auto p-4">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-display mb-6 text-parchment-100 text-shadow-golden">
          {t().professors.title}
        </h1>
        <RequireRole minRole="creator">
          <Button variant="primary" onClick={() => setShowCreateForm(true)}>
            {t().professors.addProfessor}
          </Button>
        </RequireRole>
      </div>

      <Show when={showCreateForm()}>
        <RequireRole minRole="creator">
          <div class="arcane-card p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4 text-parchment-100">
              {t().professors.createNewProfessor}
            </h2>
            <ProfessorForm
              onSubmit={handleSubmitCreate}
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
            name="searchProfessors"
            type="text"
            value={searchQuery()}
            onInput={(e) => setSearchQuery(e.currentTarget.value)}
            placeholder={t().professors.searchPlaceholder}
            inputClass="flex-1"
          />
          <Button type="submit" variant="secondary" class="shrink-0">
            {t().common.search}
          </Button>
        </div>
        {/* Faculty and Department dropdowns - on their own line */}
        <div class="flex flex-col sm:flex-row gap-2">
          <Show
            when={!faculties.loading && faculties()?.items}
            fallback={
              <div class="w-full sm:w-auto sm:min-w-64 px-4 py-2 border rounded-lg bg-arcanum-800 border-parchment-700/30 text-parchment-300 flex items-center">
                {t().professors.loadingFaculties}
              </div>
            }
          >
            <Select
              name="faculty"
              options={facultyOptions()}
              value={selectedFacultyId() ?? 'all'}
              onChange={handleFacultyChange}
              placeholder={t().professors.allFaculties}
              class="w-full sm:w-auto sm:min-w-64 sm:max-w-md"
            />
          </Show>
          <Show
            when={!departments.loading && departments()?.items}
            fallback={
              <div class="w-full sm:w-auto sm:min-w-64 px-4 py-2 border rounded-lg bg-arcanum-800 border-parchment-700/30 text-parchment-300 flex items-center">
                {t().professors.loadingDepartments}
              </div>
            }
          >
            <Select
              name="department"
              options={departmentOptions()}
              value={selectedDepartmentId() ?? 'all'}
              onChange={handleDepartmentChange}
              placeholder={t().professors.allDepartments}
              class="w-full sm:w-auto sm:min-w-64 sm:max-w-md"
            />
          </Show>
        </div>
      </form>

      {/* Professors List */}
      <Show
        when={!professorsResource.loading}
        fallback={<p class="text-muted text-center py-8">{t().professors.loading}</p>}
      >
        <Show
          when={!professorsResource.error}
          fallback={
            <div class="text-danger text-center py-8">
              <p>
                {t().professors.errorLoading}:{' '}
                {professorsResource.error instanceof Error
                  ? professorsResource.error.message
                  : t().common.unknownError}
              </p>
              <Button variant="ghost" onClick={() => void refetch()} class="mt-4">
                {t().common.retry}
              </Button>
            </div>
          }
        >
          <Show
            when={professorsResource()?.items.length}
            fallback={<div class="text-center py-8">{t().professors.noProfessorsFound}</div>}
          >
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <For each={professorsResource()?.items}>
                {(professor: Professor) => <ProfessorListItem professor={professor} />}
              </For>
            </div>

            {/* Pagination */}
            <div class="mt-8 flex justify-center gap-2">
              <Button
                variant="outline"
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page() <= 1}
              >
                {t().common.previous}
              </Button>
              <span class="px-4 py-2 flex items-center text-muted">
                {t().common.page} {page()} {t().common.of} {professorsResource()?.pages || 1}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={page() >= (professorsResource()?.pages || 1)}
              >
                {t().common.next}
              </Button>
            </div>
          </Show>
        </Show>
      </Show>
    </main>
  )
}
