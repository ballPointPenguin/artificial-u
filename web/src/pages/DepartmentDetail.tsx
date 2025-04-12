import { A, useNavigate, useParams } from '@solidjs/router'
import { Show, createResource, createSignal } from 'solid-js'
import {
  deleteDepartment,
  getDepartment,
  updateDepartment,
} from '../api/services/department-service'
import type { Department } from '../api/types'
import ConfirmationModal from '../components/ConfirmationModal'
import DepartmentForm from '../components/DepartmentForm'
import { Button } from '../components/ui/Button'

const DepartmentDetail = () => {
  const params = useParams()
  const navigate = useNavigate()
  const [isEditing, setIsEditing] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')

  // Create a resource to fetch the department data
  const [department, { refetch }] = createResource(() => {
    const id = Number.parseInt(params.id, 10)
    if (Number.isNaN(id)) {
      throw new Error('Invalid department ID')
    }
    return id
  }, getDepartment)

  const handleSubmitUpdate = async (formData: FormData) => {
    setIsSubmitting(true)
    setError('')

    try {
      const id = Number.parseInt(params.id, 10)
      if (Number.isNaN(id)) {
        throw new Error('Invalid department ID')
      }

      const updatedDepartment = {
        name: formData.get('name') as string,
        code: formData.get('code') as string,
        faculty: formData.get('faculty') as string,
        description: formData.get('description') as string,
      }

      await updateDepartment(id, updatedDepartment)
      setIsEditing(false)
      void refetch()
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'Failed to update department'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    setIsSubmitting(true)
    setError('')

    try {
      const id = Number.parseInt(params.id, 10)
      if (Number.isNaN(id)) {
        throw new Error('Invalid department ID')
      }

      await deleteDepartment(id)
      // Navigate back to departments list after deletion
      navigate('/academics/departments')
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'Failed to delete department'
      )
      setIsDeleting(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div class="container mx-auto px-4 py-8">
      {/* Breadcrumb navigation - Use theme colors */}
      <div class="mb-6">
        <A
          href="/academics/departments"
          class="text-mystic-500 hover:text-mystic-300"
        >
          ← Back to Departments
        </A>
      </div>

      {/* Loading and error states */}
      <Show
        when={!department.loading}
        fallback={
          <div class="text-center py-8 text-parchment-300">
            Loading department information...
          </div>
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
              <div class="bg-arcanum-900 border border-parchment-800/30 rounded-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Edit Department</h2>
                <DepartmentForm
                  department={department() as Department}
                  onSubmit={(formData) => void handleSubmitUpdate(formData)}
                  onCancel={() => setIsEditing(false)}
                  isSubmitting={isSubmitting()}
                  error={error()}
                />
              </div>
            }
          >
            {/* Department details */}
            <div class="bg-arcanum-900 border border-parchment-800/30 rounded-lg overflow-hidden">
              <div class="p-6">
                <div class="flex justify-between items-center mb-4">
                  <h1 class="text-3xl font-bold">{department()?.name}</h1>
                  <div class="flex space-x-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setIsEditing(true)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsDeleting(true)}
                      class="border-red-500/50 text-red-300 hover:bg-red-900/30 hover:border-red-500"
                    >
                      Delete
                    </Button>
                  </div>
                </div>

                <div class="mb-6">
                  <h2 class="text-xl font-semibold mb-2 text-parchment-100">
                    Description
                  </h2>
                  <p class="text-parchment-200 whitespace-pre-line">
                    {department()?.description}
                  </p>
                </div>

                <div class="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <h3 class="font-medium text-parchment-400">
                      Department Code
                    </h3>
                    <p>{department()?.code}</p>
                  </div>
                  <div>
                    <h3 class="font-medium text-parchment-400">Faculty</h3>
                    <p>{department()?.faculty}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Related sections - placeholder for future expansion */}
            <div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="bg-arcanum-900 border border-parchment-800/30 rounded-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Courses</h2>
                <p class="text-parchment-300">
                  This section will display courses in this department.
                </p>
                <Button variant="link" size="sm" class="mt-4" disabled>
                  View All Courses
                </Button>
              </div>

              <div class="bg-arcanum-900 border border-parchment-800/30 rounded-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Professors</h2>
                <p class="text-parchment-300">
                  This section will display professors in this department.
                </p>
                <Button variant="link" size="sm" class="mt-4" disabled>
                  View All Professors
                </Button>
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
