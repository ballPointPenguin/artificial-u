import { createResource, createSignal, For, Show } from 'solid-js'
import { preferenceService } from '../api/services/preference-service'
import { Button, Card, FormField, Input } from '../components/ui'

/** Well-known model identifiers shown as quick-pick suggestions. */
const SUGGESTED_MODELS = [
  'claude-sonnet-5',
  'claude-opus-4-8',
  'claude-opus-4-6',
  'claude-sonnet-4-6',
  'claude-haiku-4-5',
  'gpt-5.5',
  'gpt-5.4-nano',
  'gemini-3.5-flash',
  'gemini-3.1-pro-preview',
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
        setSelectedModel('')
        return { model: '', source: 'environment' as const }
      }
    }
  })

  const handleSave = async () => {
    const model = selectedModel().trim()
    if (!model) {
      setErrorMessage('Please enter a model name')
      setTimeout(() => setErrorMessage(null), 3000)
      return
    }

    setIsSaving(true)
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      await preferenceService.setGlobal(LECTURE_GENERATION_MODEL_SCOPE, model)
      setSuccessMessage(`Lecture generation model updated to "${model}"`)
      setTimeout(() => setSuccessMessage(null), 3000)
      void refetch()
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to update model setting')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setIsSaving(false)
    }
  }

  const handleClear = async () => {
    setIsSaving(true)
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      await preferenceService.deleteGlobal(LECTURE_GENERATION_MODEL_SCOPE)
      setSelectedModel('')
      setSuccessMessage('Preference cleared — will use environment default')
      setTimeout(() => setSuccessMessage(null), 3000)
      void refetch()
    } catch {
      // 404 is fine — means there was no preference to delete
      setSelectedModel('')
      setSuccessMessage('Preference cleared — will use environment default')
      setTimeout(() => setSuccessMessage(null), 3000)
      void refetch()
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <main class="container mx-auto p-4">
      <div class="mb-6">
        <h1 class="text-3xl font-display text-parchment-100 text-shadow-golden">Settings</h1>
        <p class="mt-1 text-sm text-muted font-serif">Configure admin-wide preferences.</p>
      </div>

      {/* Success/Error Messages */}
      <Show when={successMessage()}>
        <div class="mb-4 rounded-md border border-success-border bg-success-bg p-4 text-success">
          {successMessage()}
        </div>
      </Show>

      <Show when={errorMessage()}>
        <div class="mb-4 rounded-md border border-danger-border bg-danger-bg p-4 text-danger">
          {errorMessage()}
        </div>
      </Show>

      {/* Lecture Generation Model Settings */}
      <Card class="mb-6">
        <div class="space-y-4">
          <div>
            <h2 class="mb-2 text-2xl font-semibold">Lecture Generation Model</h2>
            <p class="text-muted text-sm">
              Set the AI model used for generating lecture content. This overrides the environment
              default for all lecture generation requests. You can type any valid model identifier.
            </p>
          </div>

          <Show
            when={!currentModelResource.loading}
            fallback={<div class="text-muted">Loading current settings...</div>}
          >
            <Show when={currentModelResource()}>
              {(resource) => (
                <div class="mb-4 rounded-md border border-info-border bg-info-bg p-3 text-sm text-info">
                  <strong>Current model:</strong>{' '}
                  <code class="rounded bg-surface px-1.5 py-0.5 font-mono text-xs">
                    {resource().model || '(none)'}
                  </code>
                  <br />
                  <strong>Source:</strong>{' '}
                  {resource().source === 'preference' ? 'Custom preference' : 'Environment default'}
                </div>
              )}
            </Show>
          </Show>

          <FormField label="Model Name" name="model-input">
            <Input
              name="model-input"
              value={selectedModel()}
              onChange={(value) => setSelectedModel(value)}
              placeholder="e.g. claude-opus-4-6"
              disabled={isSaving()}
              type="text"
            />
          </FormField>

          {/* Quick-pick suggestions */}
          <div>
            <p class="text-muted mb-2 text-xs font-medium">Quick suggestions:</p>
            <div class="flex flex-wrap gap-2">
              <For each={SUGGESTED_MODELS}>
                {(model) => (
                  <button
                    type="button"
                    class={`rounded-md border px-3 py-1 text-xs font-mono transition-colors ${
                      selectedModel() === model
                        ? 'border-accent bg-accent/15 text-accent'
                        : 'border-border bg-surface hover:bg-muted/30'
                    }`}
                    onClick={() => setSelectedModel(model)}
                    disabled={isSaving()}
                  >
                    {model}
                  </button>
                )}
              </For>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <Button onClick={() => void handleClear()} disabled={isSaving()} variant="outline">
              Reset to Default
            </Button>
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
          <p class="text-muted text-sm">
            Additional settings will be added here in future updates:
          </p>
          <ul class="text-muted ml-6 list-disc text-sm">
            <li>Summary generation model selection</li>
            <li>Topic generation model selection</li>
            <li>Default voice selection preferences</li>
            <li>Content generation parameters (word count, style, etc.)</li>
          </ul>
        </div>
      </Card>
    </main>
  )
}
