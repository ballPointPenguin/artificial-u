import { createResource, createSignal, For, Show } from 'solid-js'
import {
  type ElevenLabsAccountStatus,
  elevenLabsAdminService,
} from '../api/services/elevenlabs-admin-service'
import { type ModelSettingResponse, preferenceService } from '../api/services/preference-service'
import { Button, Card, FormField, Input } from '../components/ui'

/** Well-known model identifiers shown as quick-pick suggestions. */
const SUGGESTED_MODELS = [
  'claude-opus-5-5',
  'claude-opus-5',
  'claude-sonnet-5-5',
  'claude-sonnet-5',
  'claude-haiku-4-5',
  'gpt-6-sol',
  'gpt-6-luna',
  'gpt-5.6',
  'gemini-3.8-flash',
  'gemini-3.1-pro-preview',
  'grok-4.7',
]

/** One admin-wide model preference: shows the current model, quick picks, save and reset. */
function ModelSettingCard(props: {
  title: string
  description: string
  scope: string
  load: () => Promise<ModelSettingResponse>
  setSuccess: (message: string | null) => void
  setError: (message: string | null) => void
}) {
  const [selectedModel, setSelectedModel] = createSignal<string>('')
  const [isSaving, setIsSaving] = createSignal(false)
  // Load current model preference
  const [currentModelResource, { refetch }] = createResource(async () => {
    try {
      const response = await props.load()
      setSelectedModel(response.model)
      return response
    } catch {
      // If the model endpoint fails, try the raw global preference
      try {
        const pref = await preferenceService.getGlobal(props.scope)
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
      props.setError('Please enter a model name')
      setTimeout(() => {
        props.setError(null)
      }, 3000)
      return
    }

    setIsSaving(true)
    props.setError(null)
    props.setSuccess(null)

    try {
      await preferenceService.setGlobal(props.scope, model)
      props.setSuccess(`${props.title} updated to "${model}"`)
      setTimeout(() => {
        props.setSuccess(null)
      }, 3000)
      void refetch()
    } catch (error) {
      props.setError(error instanceof Error ? error.message : 'Failed to update model setting')
      setTimeout(() => {
        props.setError(null)
      }, 5000)
    } finally {
      setIsSaving(false)
    }
  }

  const handleClear = async () => {
    setIsSaving(true)
    props.setError(null)
    props.setSuccess(null)

    try {
      await preferenceService.deleteGlobal(props.scope)
      setSelectedModel('')
      props.setSuccess('Preference cleared — will use environment default')
      setTimeout(() => {
        props.setSuccess(null)
      }, 3000)
      void refetch()
    } catch {
      // 404 is fine — means there was no preference to delete
      setSelectedModel('')
      props.setSuccess('Preference cleared — will use environment default')
      setTimeout(() => {
        props.setSuccess(null)
      }, 3000)
      void refetch()
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card class="mb-6">
      <div class="space-y-4">
        <div>
          <h2 class="mb-2 text-2xl font-semibold">{props.title}</h2>
          <p class="text-muted text-sm">
            {props.description} This overrides the environment default. You can type any valid model
            identifier.
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

        <FormField label="Model Name" name={`${props.scope}-input`}>
          <Input
            name={`${props.scope}-input`}
            value={selectedModel()}
            onChange={(value) => setSelectedModel(value)}
            placeholder="e.g. claude-opus-5"
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
  )
}

const formatNumber = (n: number | null) => (n === null ? '—' : n.toLocaleString())
const formatDate = (iso: string | null) => (iso ? new Date(iso).toLocaleString() : '—')

function AccountRow(props: { account: ElevenLabsAccountStatus }) {
  const a = () => props.account
  return (
    <div class="rounded-md border border-border p-3 text-sm">
      <div class="mb-2 flex items-center gap-2">
        <strong class="capitalize">{a().label} account</strong>
        <Show when={a().active}>
          <span class="rounded bg-accent/15 px-2 py-0.5 text-xs text-accent">In use</span>
        </Show>
        <Show when={a().configured && a().tier}>
          <span class="text-muted text-xs">
            {a().tier} · {a().status}
          </span>
        </Show>
      </div>
      <Show when={a().configured} fallback={<p class="text-muted">Not configured.</p>}>
        <Show
          when={!a().error}
          fallback={<p class="text-danger">Usage unavailable: {a().error}</p>}
        >
          <div class="mb-1 h-2 overflow-hidden rounded bg-surface">
            <div
              class="h-full bg-accent"
              style={{ width: `${String(Math.min(a().percent_used ?? 0, 100))}%` }}
            />
          </div>
          <p>
            {formatNumber(a().character_count)} / {formatNumber(a().character_limit)} characters
            used ({a().percent_used ?? 0}%) · {formatNumber(a().characters_remaining)} remaining
          </p>
          <p class="text-muted">
            Resets {formatDate(a().next_reset_at)}
            {a().billing_period ? ` · ${a().billing_period ?? ''} billing` : ''}
          </p>
        </Show>
      </Show>
    </div>
  )
}

/** Shows which ElevenLabs account is serving TTS, usage per account, and a manual reset. */
function ElevenLabsStatusCard(props: {
  setSuccess: (message: string | null) => void
  setError: (message: string | null) => void
}) {
  const [status, { refetch }] = createResource(() => elevenLabsAdminService.getStatus())
  const [isResetting, setIsResetting] = createSignal(false)

  const handleReset = async () => {
    setIsResetting(true)
    props.setError(null)
    try {
      await elevenLabsAdminService.reset()
      props.setSuccess('Switched back to the primary ElevenLabs account')
      setTimeout(() => {
        props.setSuccess(null)
      }, 3000)
      void refetch()
    } catch (error) {
      props.setError(error instanceof Error ? error.message : 'Failed to reset failover')
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <Card class="mb-6">
      <div class="space-y-4">
        <div>
          <h2 class="mb-2 text-2xl font-semibold">ElevenLabs Accounts</h2>
          <p class="text-muted text-sm">
            Text-to-speech uses the primary account until its quota is exhausted, then the alternate
            account until the primary's quota resets.
          </p>
        </div>
        <Show when={!status.loading} fallback={<div class="text-muted">Loading usage...</div>}>
          <Show
            when={status()}
            fallback={<div class="text-danger">Could not load ElevenLabs status.</div>}
          >
            {(s) => (
              <>
                <Show
                  when={s().failover_enabled}
                  fallback={
                    <p class="text-muted text-sm">
                      No alternate account configured (set ELEVENLABS_API_KEY_ALT).
                    </p>
                  }
                >
                  <div class="rounded-md border border-info-border bg-info-bg p-3 text-sm text-info">
                    <strong>Active:</strong> {s().active_account} account
                    <Show when={s().failover_until}>
                      {' '}
                      — returns to primary {formatDate(s().failover_until)}
                    </Show>
                  </div>
                </Show>
                <For each={s().accounts}>{(account) => <AccountRow account={account} />}</For>
                <div class="flex justify-end gap-2">
                  <Button onClick={() => void refetch()} variant="outline">
                    Refresh
                  </Button>
                  <Show when={s().active_account === 'alt'}>
                    <Button
                      onClick={() => void handleReset()}
                      disabled={isResetting()}
                      variant="primary"
                    >
                      {isResetting() ? 'Resetting...' : 'Switch to primary now'}
                    </Button>
                  </Show>
                </div>
              </>
            )}
          </Show>
        </Show>
      </div>
    </Card>
  )
}

export default function AdminSettings() {
  const [successMessage, setSuccessMessage] = createSignal<string | null>(null)
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null)

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

      <ModelSettingCard
        title="Lecture Generation Model"
        description="Set the AI model used for generating lecture content."
        scope="LECTURE_GENERATION_MODEL"
        load={preferenceService.getLectureGenerationModel}
        setSuccess={setSuccessMessage}
        setError={setErrorMessage}
      />

      <ModelSettingCard
        title="Topics Generation Model"
        description="Set the AI model used for generating course topics."
        scope="TOPICS_GENERATION_MODEL"
        load={preferenceService.getTopicsGenerationModel}
        setSuccess={setSuccessMessage}
        setError={setErrorMessage}
      />

      <ElevenLabsStatusCard setSuccess={setSuccessMessage} setError={setErrorMessage} />

      {/* Future Settings Sections */}
      <Card class="opacity-50">
        <div class="space-y-2">
          <h2 class="text-xl font-semibold">Future Settings</h2>
          <p class="text-muted text-sm">
            Additional settings will be added here in future updates:
          </p>
          <ul class="text-muted ml-6 list-disc text-sm">
            <li>Summary generation model selection</li>
            <li>Default voice selection preferences</li>
            <li>Content generation parameters (word count, style, etc.)</li>
          </ul>
        </div>
      </Card>
    </main>
  )
}
