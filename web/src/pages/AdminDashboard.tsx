import { createMemo, createResource, createSignal, For, Show } from 'solid-js'
import { studentService } from '../api/services/student-service'
import type { Student } from '../api/types'
import { Button, Card, FormField, NumberInput, Select, type SelectOption } from '../components/ui'

const ROLE_OPTIONS: SelectOption[] = [
  { value: 'viewer', label: 'Viewer' },
  { value: 'creator', label: 'Creator' },
  { value: 'admin', label: 'Admin' },
]

export default function AdminDashboard() {
  const [currentPage, setCurrentPage] = createSignal(1)
  const [pageSize] = createSignal(10)
  const [roleFilter, setRoleFilter] = createSignal<'viewer' | 'creator' | 'admin' | undefined>(
    undefined
  )
  const [coinAmounts, setCoinAmounts] = createSignal<Partial<Record<number, number>>>({})
  const [updatingRoles, setUpdatingRoles] = createSignal<Set<number>>(new Set())
  const [addingCoins, setAddingCoins] = createSignal<Set<number>>(new Set())
  const [successMessage, setSuccessMessage] = createSignal<string | null>(null)
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null)
  const [deletingStudents, setDeletingStudents] = createSignal<Set<number>>(new Set())

  const [studentsResource, { refetch }] = createResource(
    () => ({
      page: currentPage(),
      size: pageSize(),
      role: roleFilter(),
    }),
    (params) => studentService.listStudents(params)
  )

  const handleRoleChange = async (studentId: number, newRole: 'viewer' | 'creator' | 'admin') => {
    setUpdatingRoles((prev) => {
      const next = new Set(prev)
      next.add(studentId)
      return next
    })
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      await studentService.updateStudentRole(studentId, newRole)
      setSuccessMessage(`Role updated successfully for student ${String(studentId)}`)
      setTimeout(() => setSuccessMessage(null), 3000)
      void refetch()
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to update role')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setUpdatingRoles((prev) => {
        const next = new Set(prev)
        next.delete(studentId)
        return next
      })
    }
  }

  const handleAddCoins = async (studentId: number) => {
    const amount = coinAmounts()[studentId]
    if (amount === undefined || amount === 0) {
      setErrorMessage('Enter a non-zero coin adjustment')
      setTimeout(() => setErrorMessage(null), 3000)
      return
    }

    setAddingCoins((prev) => {
      const next = new Set(prev)
      next.add(studentId)
      return next
    })
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      await studentService.addStudentCoins(studentId, amount)
      setSuccessMessage(`Adjusted student ${String(studentId)} by ${String(amount)} coins`)
      setTimeout(() => setSuccessMessage(null), 3000)
      setCoinAmounts((prev) => {
        const { [studentId]: removedValue, ...rest } = prev
        void removedValue
        return rest
      })
      void refetch()
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to add coins')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setAddingCoins((prev) => {
        const next = new Set(prev)
        next.delete(studentId)
        return next
      })
    }
  }

  const handleDeleteStudent = async (student: Student) => {
    const confirmed = window.confirm(
      `Delete ${student.name || `student ${String(student.id)}`}? This only removes their account and keeps any created resources.`
    )
    if (!confirmed) {
      return
    }

    setDeletingStudents((prev) => {
      const next = new Set(prev)
      next.add(student.id)
      return next
    })
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      await studentService.deleteStudent(student.id)
      setSuccessMessage(`Deleted student ${student.name || String(student.id)}`)
      setTimeout(() => setSuccessMessage(null), 3000)
      setCoinAmounts((prev) => {
        const { [student.id]: removedValue, ...rest } = prev
        void removedValue
        return rest
      })
      void refetch()
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to delete student')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setDeletingStudents((prev) => {
        const next = new Set(prev)
        next.delete(student.id)
        return next
      })
    }
  }

  const updateCoinAmount = (studentId: number, value: string) => {
    const numValue = Number.parseInt(value, 10)
    setCoinAmounts((prev) => ({
      ...prev,
      [studentId]: Number.isNaN(numValue) || value === '' ? undefined : numValue,
    }))
  }

  const students = () => studentsResource()?.items ?? []
  const sortedStudents = createMemo(() => [...students()].sort((a, b) => b.id - a.id))
  const total = () => studentsResource()?.total ?? 0
  const pages = () => studentsResource()?.pages ?? 1
  const currentPageNum = () => studentsResource()?.page ?? 1

  return (
    <main class="container mx-auto p-4">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-display mb-6 text-parchment-100 text-shadow-golden">
          Admin Dashboard
        </h1>
        <div class="flex items-center gap-3">
          <a
            href="/admin/featured"
            class="rounded-md border border-border bg-muted/30 px-4 py-2 text-sm font-medium transition-colors hover:bg-muted/60"
          >
            Featured
          </a>
          <a
            href="/admin/settings"
            class="rounded-md border border-border bg-muted/30 px-4 py-2 text-sm font-medium transition-colors hover:bg-muted/60"
          >
            Settings
          </a>
          <Button
            variant="secondary"
            onClick={() => {
              void refetch()
            }}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Success/Error Messages */}
      <Show when={successMessage()}>
        <Card class="mb-4 border-green-500 bg-green-100 dark:bg-green-900/30">
          <p class="text-green-800 dark:text-green-200">{successMessage()}</p>
        </Card>
      </Show>
      <Show when={errorMessage()}>
        <Card class="mb-4 border-red-500 bg-red-100 dark:bg-red-900/30">
          <p class="text-red-800 dark:text-red-200">{errorMessage()}</p>
        </Card>
      </Show>

      {/* Role Filter */}
      <div class="mb-6">
        <FormField label="Filter by Role" name="role-filter">
          <Select
            name="role-filter"
            value={roleFilter() || null}
            onChange={(value) => {
              if (!value) {
                setRoleFilter(undefined)
                return
              }
              setRoleFilter(value as 'viewer' | 'creator' | 'admin')
            }}
            options={[{ value: '', label: 'All Roles' }, ...ROLE_OPTIONS]}
            placeholder="All Roles"
          />
        </FormField>
      </div>

      {/* Students Table */}
      <Show
        when={!studentsResource.loading}
        fallback={<p class="text-muted text-center py-8">Loading students...</p>}
      >
        <Show
          when={!studentsResource.error}
          fallback={
            <div class="text-danger text-center py-8">
              <p>
                Error loading students:{' '}
                {studentsResource.error instanceof Error
                  ? studentsResource.error.message
                  : 'Unknown error'}
              </p>
              <Button
                variant="ghost"
                onClick={() => {
                  void refetch()
                }}
                class="mt-4"
              >
                Retry
              </Button>
            </div>
          }
        >
          <Show
            when={sortedStudents().length > 0}
            fallback={<div class="text-center py-8">No students found</div>}
          >
            <div class="arcane-card overflow-x-auto">
              <table class="min-w-full divide-y divide-border">
                <thead class="bg-muted/50">
                  <tr>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      ID
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Name
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Email
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Role
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Coins
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Active
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                    >
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-background divide-y divide-border">
                  <For each={sortedStudents()}>
                    {(student: Student) => {
                      const currentAmount = () => coinAmounts()[student.id]
                      const hasValidAmount = () => {
                        const value = currentAmount()
                        return typeof value === 'number' && value !== 0
                      }

                      return (
                        <tr class="hover:bg-muted/30 transition-colors">
                          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            {student.id}
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap text-sm">{student.name}</td>
                          <td class="px-6 py-4 whitespace-nowrap text-sm text-muted">
                            {student.email || '-'}
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <Select
                              name={`role-${String(student.id)}`}
                              value={student.role}
                              onChange={(value) => {
                                if (value && value !== student.role) {
                                  void handleRoleChange(
                                    student.id,
                                    value as 'viewer' | 'creator' | 'admin'
                                  )
                                }
                              }}
                              options={ROLE_OPTIONS}
                              disabled={updatingRoles().has(student.id)}
                              class="min-w-[120px]"
                            />
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                            {student.coins}
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <span
                              class={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                student.is_active
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200'
                              }`}
                            >
                              {student.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <div class="flex flex-col gap-2">
                              <div class="flex items-center gap-2">
                                <NumberInput
                                  name={`coins-${String(student.id)}`}
                                  value={
                                    currentAmount() !== undefined ? String(currentAmount()) : ''
                                  }
                                  onInput={(
                                    event: InputEvent & { currentTarget: HTMLInputElement }
                                  ) => {
                                    updateCoinAmount(student.id, event.currentTarget.value)
                                  }}
                                  placeholder="Amount (+/-)"
                                  class="w-24"
                                  disabled={addingCoins().has(student.id)}
                                />
                                <Button
                                  variant="primary"
                                  onClick={() => {
                                    void handleAddCoins(student.id)
                                  }}
                                  disabled={addingCoins().has(student.id) || !hasValidAmount()}
                                >
                                  {addingCoins().has(student.id) ? 'Adding...' : 'Add Coins'}
                                </Button>
                              </div>
                              <Button
                                variant="danger"
                                size="sm"
                                onClick={() => {
                                  void handleDeleteStudent(student)
                                }}
                                disabled={deletingStudents().has(student.id)}
                              >
                                {deletingStudents().has(student.id) ? 'Deleting...' : 'Delete'}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      )
                    }}
                  </For>
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div class="mt-6 flex items-center justify-between">
              <div class="text-sm text-muted">
                Showing {sortedStudents().length} of {total()} students (Page {currentPageNum()} of{' '}
                {pages()})
              </div>
              <div class="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPageNum() <= 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage((p) => Math.min(pages(), p + 1))}
                  disabled={currentPageNum() >= pages()}
                >
                  Next
                </Button>
              </div>
            </div>
          </Show>
        </Show>
      </Show>
    </main>
  )
}
