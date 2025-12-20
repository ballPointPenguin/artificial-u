import { createResource, createSignal, Show } from 'solid-js'
import { preferenceService } from '../api/services/preference-service'
import { Button, Card, FormField, Select, type SelectOption } from '../components/ui'

const MODEL_OPTIONS: SelectOption[] = [
  { value: 'claude-opus-4-5', label: 'Claude Opus 4.5 (Highest Quality)' },
  { value: 'claude-sonnet-4-5', label: 'Claude Sonnet 4.5 (Balanced)' },
  { value: 'claude-haiku-4-5', label: 'Claude Haiku 4.5 (Fastest)' },
]

const LECTURE_GENERATION_MODEL_SCOPE = 'LECTURE_GENERATION_MODEL'

export default function AdminSettings() {
  const [selectedModel, setSelectedModel] = createSignal<string>('')
  const [isSaving, setIsSaving] = createSignal(false)
  const [successMessage, setSuccessMessage] = createSignal<string | null>(null)
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null)

  // Load current model preference
  const [currentModelResource, { refetch }] = createResource(async () => {
    try {
      const response = await preferenceService.getLectureGenerationModel()
      setSelectedModel(response.model)
      return response
    } catch {
      // If no preference is set, try to get from global preferences
      try {
        const pref = await preferenceService.getGlobal(LECTURE_GENERATION_MODEL_SCOPE)
        setSelectedModel(pref.value)
        return { model: pref.value, source: 'preference' as const }
      } catch {
        // Default to first option if nothing is set
        const defaultValue = String(MODEL_OPTIONS[0].value)
        setSelectedModel(defaultValue)
        return { model: defaultValue, source: 'environment' as const }
      }
    }
  })

  const handleSave = async () => {
    const model = selectedModel()
    if (!model) {
      setErrorMessage('Please select a model')
      setTimeout(() => setErrorMessage(null), 3000)
      return
    }

    setIsSaving(true)
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      await preferenceService.setGlobal(LECTURE_GENERATION_MODEL_SCOPE, model)
      setSuccessMessage('Lecture generation model updated successfully!')
      setTimeout(() => setSuccessMessage(null), 3000)
      void refetch()
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to update model setting')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div class="container mx-auto max-w-4xl px-4 py-8">
      <h1 class="mb-6 text-3xl font-bold">Admin Settings</h1>

      {/* Success/Error Messages */}
      <Show when={successMessage()}>
        <div class="mb-4 rounded-md bg-green-100 p-4 text-green-800 dark:bg-green-900 dark:text-green-200">
          {successMessage()}
        </div>
      </Show>

      <Show when={errorMessage()}>
        <div class="mb-4 rounded-md bg-red-100 p-4 text-red-800 dark:bg-red-900 dark:text-red-200">
          {errorMessage()}
        </div>
      </Show>

      {/* Lecture Generation Model Settings */}
      <Card class="mb-6">
        <div class="space-y-4">
          <div>
            <h2 class="mb-2 text-2xl font-semibold">Lecture Generation Model</h2>
            <p class="text-muted-foreground text-sm">
              Select the AI model to use for generating lecture content. This setting applies
              globally to all lecture generation requests.
            </p>
          </div>

          <Show
            when={!currentModelResource.loading}
            fallback={<div class="text-muted-foreground">Loading current settings...</div>}
          >
            <Show when={currentModelResource()}>
              {(resource) => (
                <div class="mb-4 rounded-md bg-blue-50 p-3 text-sm dark:bg-blue-900/20">
                  <strong>Current model:</strong> {resource().model}
                  <br />
                  <strong>Source:</strong>{' '}
                  {resource().source === 'preference' ? 'Custom preference' : 'Environment default'}
                </div>
              )}
            </Show>
          </Show>

          <FormField label="Model Selection" name="model-select">
            <Select
              name="model-select"
              value={selectedModel()}
              onChange={(value) => setSelectedModel(value ? String(value) : '')}
              options={MODEL_OPTIONS}
              disabled={isSaving()}
              placeholder="Select a model..."
            />
          </FormField>

          <div class="rounded-md bg-amber-50 p-4 text-sm dark:bg-amber-900/20">
            <p class="font-semibold">Model Comparison:</p>
            <ul class="ml-4 mt-2 list-disc space-y-1 text-xs">
              <li>
                <strong>Opus 4.5:</strong> Highest quality, slowest
              </li>
              <li>
                <strong>Sonnet 4.5:</strong> Balanced quality and speed
              </li>
              <li>
                <strong>Haiku 4.5:</strong> Fastest generation, fair quality
              </li>
            </ul>
          </div>

          <div class="flex justify-end gap-2">
            <Button onClick={() => void handleSave()} disabled={isSaving()} variant="primary">
              {isSaving() ? 'Saving...' : 'Save Settings'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Future Settings Sections */}
      <Card class="opacity-50">
        <div class="space-y-2">
          <h2 class="text-xl font-semibold">Future Settings</h2>
          <p class="text-muted-foreground text-sm">
            Additional settings will be added here in future updates:
          </p>
          <ul class="text-muted-foreground ml-6 list-disc text-sm">
            <li>Summary generation model selection</li>
            <li>Topic generation model selection</li>
            <li>Default voice selection preferences</li>
            <li>Content generation parameters (word count, style, etc.)</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}
