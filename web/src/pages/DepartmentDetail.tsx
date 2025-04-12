import { A, useParams } from '@solidjs/router'
import { Show, createResource } from 'solid-js'
import { getDepartment } from '../api/services/department-service'

const DepartmentDetail = () => {
  const params = useParams()

  // Create a resource to fetch the department data
  const [department, { refetch }] = createResource(() => {
    const id = Number.parseInt(params.id, 10)
    if (Number.isNaN(id)) {
      throw new Error('Invalid department ID')
    }
    return id
  }, getDepartment)

  return (
    <div class="container mx-auto px-4 py-8">
      {/* Breadcrumb navigation */}
      <div class="mb-6">
        <A href="/departments" class="text-blue-600 hover:text-blue-800">
          ← Back to Departments
        </A>
      </div>

      {/* Loading and error states */}
      <Show
        when={!department.loading}
        fallback={
          <div class="text-center py-8">Loading department information...</div>
        }
      >
        <Show
          when={!department.error}
          fallback={
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              <p>
                Error:{' '}
                {department.error instanceof Error
                  ? department.error.message
                  : 'Failed to load department'}
              </p>
              <button
                type="button"
                onClick={() => void refetch()}
                class="mt-2 text-blue-600 hover:text-blue-800"
              >
                Try Again
              </button>
            </div>
          }
        >
          {/* Department details */}
          <div class="bg-white shadow-md rounded-lg overflow-hidden">
            <div class="p-6">
              <h1 class="text-3xl font-bold mb-4">{department()?.name}</h1>

              <div class="mb-6">
                <h2 class="text-xl font-semibold mb-2">Description</h2>
                <p class="text-gray-700 whitespace-pre-line">
                  {department()?.description}
                </p>
              </div>

              <div class="flex items-center text-sm text-gray-500">
                <div class="mr-4">
                  <span class="font-medium">Created:</span>{' '}
                  {new Date(
                    department()?.created_at || ''
                  ).toLocaleDateString()}
                </div>
                <div>
                  <span class="font-medium">Updated:</span>{' '}
                  {new Date(
                    department()?.updated_at || ''
                  ).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>

          {/* Related sections - placeholder for future expansion */}
          <div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white shadow-md rounded-lg p-6">
              <h2 class="text-xl font-semibold mb-4">Courses</h2>
              <p class="text-gray-600">
                This section will display courses in this department.
              </p>
              <button
                type="button"
                class="mt-4 text-blue-600 hover:text-blue-800 font-medium"
                disabled
              >
                View All Courses
              </button>
            </div>

            <div class="bg-white shadow-md rounded-lg p-6">
              <h2 class="text-xl font-semibold mb-4">Professors</h2>
              <p class="text-gray-600">
                This section will display professors in this department.
              </p>
              <button
                type="button"
                class="mt-4 text-blue-600 hover:text-blue-800 font-medium"
                disabled
              >
                View All Professors
              </button>
            </div>
          </div>
        </Show>
      </Show>
    </div>
  )
}

export default DepartmentDetail
