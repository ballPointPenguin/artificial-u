import { A, useNavigate, useParams } from '@solidjs/router'
import { type Component, createResource, createSignal, For, Show } from 'solid-js'
import { departmentService } from '../api/services/department-service.js'
import type {
  DepartmentCoursesResponse,
  DepartmentProfessorsResponse,
  DepartmentUpdate,
} from '../api/types.js'
import { RequireRole } from '../auth/RequireRole'
import DepartmentForm from '../components/departments/DepartmentForm.js'
import { Button, ConfirmationModal } from '../components/ui'

// Courses List Component
const CoursesList: Component<{
  courses: () => DepartmentCoursesResponse | undefined
  loading: boolean
  error: unknown
}> = (props) => {
  return (
    <Show when={!props.loading} fallback={<div class="text-parchment-300">Loading courses...</div>}>
      <Show
        when={!props.error}
        fallback={
          <div class="text-red-300">
            Error loading courses:{' '}
            {props.error instanceof Error ? props.error.message : 'Unknown error'}
          </div>
        }
      >
        <Show
          when={props.courses()?.courses && props.courses()!.courses.length > 0}
          fallback={<div class="text-parchment-300">No courses found in this department.</div>}
        >
          <div class="space-y-3">
            <For each={props.courses()?.courses}>
              {(course) => (
                <A
                  href={`/courses/${String(course.id)}`}
                  class="block p-3 bg-arcanum-800/50 border border-parchment-700/30 rounded-sm hover:bg-arcanum-800 hover:border-primary/50 hover:shadow-arcane transition-all duration-300 group"
                >
                  <div class="flex justify-between items-start">
                    <div class="flex-1">
                      <h3 class="font-medium text-parchment-100 group-hover:text-primary transition-colors duration-300">
                        {course.code} - {course.title}
                      </h3>
                      <p class="text-sm text-parchment-400 mt-1">
                        Level: {course.level} • Credits: {course.credits}
                      </p>
                    </div>
                  </div>
                </A>
              )}
            </For>
          </div>
        </Show>
      </Show>
    </Show>
  )
}

// Professors List Component
const ProfessorsList: Component<{
  professors: () => DepartmentProfessorsResponse | undefined
  loading: boolean
  error: unknown
}> = (props) => {
  return (
    <Show
      when={!props.loading}
      fallback={<div class="text-parchment-300">Loading professors...</div>}
    >
      <Show
        when={!props.error}
        fallback={
          <div class="text-red-300">
            Error loading professors:{' '}
            {props.error instanceof Error ? props.error.message : 'Unknown error'}
          </div>
        }
      >
        <Show
          when={props.professors()?.professors && props.professors()!.professors.length > 0}
          fallback={<div class="text-parchment-300">No professors found in this department.</div>}
        >
          <div class="space-y-3">
            <For each={props.professors()?.professors}>
              {(professor) => (
                <A
                  href={`/professors/${String(professor.id)}`}
                  class="block p-3 bg-arcanum-800/50 border border-parchment-700/30 rounded-sm hover:bg-arcanum-800 hover:border-primary/50 hover:shadow-arcane transition-all duration-300 group"
                >
                  <div class="flex items-start gap-3">
                    <Show when={professor.image_url}>
                      {(imageUrl) => (
                        <img
                          src={imageUrl()}
                          alt={professor.name}
                          class="w-12 h-12 object-cover rounded-sm border border-parchment-500/20 flex-shrink-0"
                        />
                      )}
                    </Show>
                    <div class="flex-1 min-w-0">
                      <h3 class="font-medium text-parchment-100 group-hover:text-primary transition-colors duration-300 truncate">
                        {professor.name}
                      </h3>
                      <p class="text-sm text-parchment-400 mt-1 truncate">
                        {professor.specialization}
                      </p>
                    </div>
                  </div>
                </A>
              )}
            </For>
          </div>
        </Show>
      </Show>
    </Show>
  )
}

const DepartmentDetail = () => {
  const params = useParams()
  const navigate = useNavigate()
  const [isEditing, setIsEditing] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')

  // Create a resource to fetch the department data
  const [department, { refetch }] = createResource(() => {
    const id = Number.parseInt(params.id ?? '', 10)
    if (Number.isNaN(id)) {
      throw new Error('Invalid department ID')
    }
    return id
  }, departmentService.getDepartment)

  // Create resources to fetch courses and professors for this department
  const [courses] = createResource(
    () => department()?.id,
    async (departmentId: number) => {
      return departmentService.getDepartmentCourses(departmentId)
    }
  )

  const [professors] = createResource(
    () => department()?.id,
    async (departmentId: number) => {
      return departmentService.getDepartmentProfessors(departmentId)
    }
  )

  const handleSubmitUpdate = async (formData: FormData) => {
    setIsSubmitting(true)
    setError('')

    try {
      const id = Number.parseInt(params.id ?? '', 10)
      if (Number.isNaN(id)) {
        throw new Error('Invalid department ID')
      }

      const facultyIdStr = formData.get('faculty_id') as string | null
      const updatedDepartmentData: DepartmentUpdate = {
        name: formData.get('name') as string,
        code: formData.get('code') as string,
        faculty_id: facultyIdStr ? Number.parseInt(facultyIdStr, 10) : null,
        description: formData.get('description') as string,
      }

      await departmentService.updateDepartment(id, updatedDepartmentData)
      setIsEditing(false)
      void refetch()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update department')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    setIsSubmitting(true)
    setError('')

    try {
      const id = Number.parseInt(params.id ?? '', 10)
      if (Number.isNaN(id)) {
        throw new Error('Invalid department ID')
      }

      await departmentService.deleteDepartment(id)
      // Navigate back to academics list after deletion
      navigate('/academics')
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to delete department')
      setIsDeleting(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div class="container mx-auto px-4 py-8">
      {/* Breadcrumb navigation - Use theme colors */}
      <div class="mb-6">
        <A href="/academics" class="text-mystic-500 hover:text-mystic-300">
          ← Back to Academics
        </A>
      </div>

      {/* Loading and error states */}
      <Show
        when={!department.loading}
        fallback={
          <div class="text-center py-8 text-parchment-300">Loading department information...</div>
        }
      >
        <Show
          when={!department.error}
          fallback={
            <div class="bg-red-900/20 border border-red-500 text-red-300 px-4 py-3 rounded">
              <p>
                Error:{' '}
                {department.error instanceof Error
                  ? department.error.message
                  : 'Failed to load department'}
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => void refetch()}
                class="mt-2 text-red-300 hover:text-red-100"
              >
                Try Again
              </Button>
            </div>
          }
        >
          <Show
            when={!isEditing()}
            fallback={
              <Show when={department()} keyed>
                {(dept) => (
                  <div class="bg-arcanum-900 border border-parchment-800/30 rounded-lg p-6">
                    <RequireRole minRole="creator">
                      <h2 class="text-xl font-semibold mb-4">Edit Department</h2>
                      <DepartmentForm
                        department={dept}
                        onSubmit={(fd) => void handleSubmitUpdate(fd)}
                        onCancel={() => setIsEditing(false)}
                        isSubmitting={isSubmitting()}
                        error={error()}
                      />
                    </RequireRole>
                  </div>
                )}
              </Show>
            }
          >
            {/* Department details */}
            <Show when={department()} keyed>
              {(dept) => (
                <div class="bg-arcanum-900 border border-parchment-800/30 rounded-lg overflow-hidden">
                  <div class="p-6">
                    <div class="flex justify-between items-center mb-4">
                      <h1 class="text-3xl font-bold">{dept.name}</h1>
                      <div class="flex space-x-2">
                        <RequireRole minRole="creator">
                          <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)}>
                            Edit
                          </Button>
                          <Button variant="danger" size="sm" onClick={() => setIsDeleting(true)}>
                            Delete
                          </Button>
                        </RequireRole>
                      </div>
                    </div>

                    <div class="mb-6">
                      <h2 class="text-xl font-semibold mb-2 text-parchment-100">Description</h2>
                      <p class="text-parchment-200 whitespace-pre-line">{dept.description}</p>
                    </div>

                    <div class="grid grid-cols-2 gap-4 mb-6">
                      <div>
                        <h3 class="font-medium text-parchment-400">Department Code</h3>
                        <p>{dept.code}</p>
                      </div>
                      <div>
                        <h3 class="font-medium text-parchment-400">Faculty</h3>
                        <p>{dept.faculty_name || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </Show>

            {/* Related sections - Courses and Professors */}
            <div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="bg-arcanum-900 border border-parchment-800/30 rounded-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Courses</h2>
                <CoursesList
                  courses={courses}
                  loading={courses.loading}
                  error={courses.error as unknown}
                />
              </div>

              <div class="bg-arcanum-900 border border-parchment-800/30 rounded-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Professors</h2>
                <ProfessorsList
                  professors={professors}
                  loading={professors.loading}
                  error={professors.error as unknown}
                />
              </div>
            </div>
          </Show>
        </Show>
      </Show>

      {/* Delete confirmation modal */}
      <ConfirmationModal
        isOpen={isDeleting()}
        title="Delete Department"
        message={
          <div>
            <p>Are you sure you want to delete this department?</p>
            <p class="mt-2 font-medium">This action cannot be undone.</p>
          </div>
        }
        confirmText="Delete Department"
        onConfirm={() => void handleDelete()}
        onCancel={() => setIsDeleting(false)}
        isConfirming={isSubmitting()}
      />
    </div>
  )
}

export default DepartmentDetail
