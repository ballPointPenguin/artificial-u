import { createSignal, onMount, Show } from 'solid-js'
import { studentService } from '../api/services'
import type { Student, StudentUpdate } from '../api/types'
import { Button, Card, FormField, Input } from '../components/ui'
import { type ContentLanguage, useContentLanguage, useTranslations } from '../i18n'

const Profile = () => {
  const t = useTranslations()
  const { contentLanguageOverride, setContentLanguage } = useContentLanguage()
  const [student, setStudent] = createSignal<Student | null>(null)
  const [isLoading, setIsLoading] = createSignal(true)
  const [isEditing, setIsEditing] = createSignal(false)
  const [isSaving, setIsSaving] = createSignal(false)
  const [error, setError] = createSignal<string | null>(null)
  const [successMessage, setSuccessMessage] = createSignal<string | null>(null)

  // Helper function to map role to enrollment status display
  const getEnrollmentStatus = (role: string): string => {
    switch (role) {
      case 'viewer':
        return t().profile.roles.viewer
      case 'creator':
        return t().profile.roles.creator
      case 'admin':
        return t().profile.roles.admin
      default:
        return role
    }
  }

  // Form state
  const [formData, setFormData] = createSignal<StudentUpdate>({
    name: '',
    email: '',
  })

  // Load student profile on mount
  onMount(() => {
    void (async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await studentService.getCurrentStudent()
        setStudent(data)
        setFormData({
          name: data.name,
          email: data.email || '',
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : t().profile.failedToLoad)
      } finally {
        setIsLoading(false)
      }
    })()
  })

  const handleEdit = () => {
    setIsEditing(true)
    setError(null)
    setSuccessMessage(null)
  }

  const handleCancel = () => {
    setIsEditing(false)
    setError(null)
    setSuccessMessage(null)
    // Reset form to current student data
    const currentStudent = student()
    if (currentStudent) {
      setFormData({
        name: currentStudent.name,
        email: currentStudent.email || '',
      })
    }
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      setError(null)
      setSuccessMessage(null)

      const updateData = formData()
      const updatedStudent = await studentService.updateCurrentStudent(updateData)
      setStudent(updatedStudent)
      setIsEditing(false)
      setSuccessMessage(t().profile.profileUpdated)

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : t().profile.failedToUpdate)
    } finally {
      setIsSaving(false)
    }
  }

  const updateFormField = (field: keyof StudentUpdate, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <div class="container mx-auto max-w-4xl px-4 py-8">
      <h1 class="text-3xl font-display mb-8">{t().profile.title}</h1>

      <Show when={isLoading()}>
        <div class="flex items-center justify-center py-12">
          <div class="text-center">
            <div class="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
            <p>{t().profile.loading}</p>
          </div>
        </div>
      </Show>

      <Show when={!isLoading() && error()}>
        <Card class="border-error-border bg-error-surface">
          <p class="text-error-text">{error()}</p>
        </Card>
      </Show>

      <Show when={!isLoading() && student()}>
        <Card class="mb-6">
          <Show when={successMessage()}>
            <div class="mb-4 rounded-lg bg-green-100 p-4 text-green-800 dark:bg-green-900/30 dark:text-green-200">
              {successMessage()}
            </div>
          </Show>

          <Show when={!isEditing()}>
            <div class="space-y-6">
              <div>
                <div class="mb-2 block text-sm font-medium opacity-70">{t().profile.name}</div>
                <p class="text-lg">{student()?.name}</p>
              </div>

              <div>
                <div class="mb-2 block text-sm font-medium opacity-70">{t().profile.email}</div>
                <p class="text-lg">{student()?.email || t().common.notProvided}</p>
              </div>

              <div class="pt-4">
                <Button onClick={handleEdit} variant="primary">
                  {t().profile.editProfile}
                </Button>
              </div>
            </div>
          </Show>

          <Show when={isEditing()}>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                void handleSave()
              }}
              class="space-y-6"
            >
              <FormField label="Name" name="name" required>
                <Input
                  name="name"
                  value={formData().name || ''}
                  onInput={(e) => {
                    updateFormField('name', e.currentTarget.value)
                  }}
                  placeholder="Enter your name"
                  required
                />
              </FormField>

              <FormField label="Email" name="email">
                <Input
                  name="email"
                  type="email"
                  value={formData().email || ''}
                  onInput={(e) => {
                    updateFormField('email', e.currentTarget.value)
                  }}
                  placeholder="Enter your email"
                />
              </FormField>

              <Show when={error() && isEditing()}>
                <div class="rounded-lg bg-red-100 p-4 text-red-800 dark:bg-red-900/30 dark:text-red-200">
                  {error()}
                </div>
              </Show>

              <div class="flex gap-4 pt-4">
                <Button type="submit" variant="primary" disabled={isSaving()}>
                  {isSaving() ? t().common.saving : t().profile.saveChanges}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleCancel}
                  disabled={isSaving()}
                >
                  {t().common.cancel}
                </Button>
              </div>
            </form>
          </Show>
        </Card>

        <div class="grid gap-6 md:grid-cols-2">
          <Card class="bg-muted">
            <h3 class="text-xl font-semibold mb-4">{t().profile.enrollmentStatus}</h3>
            <div class="space-y-4">
              <div>
                <div class="mb-1 block text-sm font-medium opacity-70">{t().profile.status}</div>
                <p class="text-2xl font-semibold">
                  {getEnrollmentStatus(student()?.role ?? 'viewer')}
                </p>
              </div>
              <div>
                <div class="mb-1 block text-sm font-medium opacity-70">
                  {t().profile.coinBalance}
                </div>
                <p class="text-2xl font-semibold">
                  {student()?.coins ?? 0} {t().profile.coins}
                </p>
              </div>
            </div>
          </Card>

          <Card class="bg-muted">
            <h3 class="text-xl font-semibold mb-4">{t().profile.accountInformation}</h3>
            <div class="space-y-2 text-sm opacity-70">
              <p>
                <strong>{t().profile.accountId}:</strong> {student()?.id}
              </p>
              <Show when={student()?.auth0_sub}>
                <p>
                  <strong>{t().profile.authId}:</strong> {student()?.auth0_sub}
                </p>
              </Show>
              <p>
                <strong>{t().profile.accountActive}:</strong>{' '}
                {student()?.is_active ? t().common.yes : t().common.no}
              </p>
            </div>
          </Card>
        </div>

        <Card class="bg-muted mt-6">
          <h3 class="text-xl font-semibold mb-1">{t().profile.contentLanguage}</h3>
          <p class="text-sm opacity-70 mb-4">{t().profile.contentLanguageDesc}</p>
          <select
            class="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            value={contentLanguageOverride() ?? 'auto'}
            onChange={(e) => {
              const val = e.currentTarget.value
              setContentLanguage(val === 'auto' ? null : (val as ContentLanguage))
            }}
          >
            <option value="auto">{t().profile.contentLanguageAuto}</option>
            <option value="en">{t().profile.contentLanguageEn}</option>
            <option value="fr">{t().profile.contentLanguageFr}</option>
          </select>
        </Card>
      </Show>
    </div>
  )
}

export default Profile
