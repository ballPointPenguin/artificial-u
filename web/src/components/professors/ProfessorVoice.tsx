import { useParams } from '@solidjs/router'
import { type Component, createMemo, createResource, createSignal, For, Show } from 'solid-js'
import { professorService } from '../../api/services/professor-service.js'
import {
  getVoice,
  listVoices,
  manualAssignVoice,
  previewVoice,
} from '../../api/services/voice-service.js'
import type { Voice } from '../../api/types.js'
import { RequireRole } from '../../auth/RequireRole'
import { Alert, Badge, Button, LoadingSpinner } from '../ui'

type TtsBackendKey = 'elevenlabs' | 'mistral'

const BACKEND_OPTIONS: Array<{ value: TtsBackendKey; label: string }> = [
  { value: 'elevenlabs', label: 'ElevenLabs' },
  { value: 'mistral', label: 'Voxtral (Mistral)' },
]

/** Display-friendly name for a gender value. */
const genderLabel = (g: string | null | undefined): string => {
  if (!g) return ''
  const map: Record<string, string> = { male: 'Male', female: 'Female', neutral: 'Neutral' }
  return map[g.toLowerCase()] ?? g
}

// ---------------------------------------------------------------------------
// Voice card shown in the browsing grid
// ---------------------------------------------------------------------------
const VoiceCard: Component<{
  voice: Voice
  isSelected: boolean
  isPreviewing: boolean
  onSelect: () => void
  onPreview: () => void
}> = (props) => {
  const attrs = createMemo(() => {
    const v = props.voice
    const items: Array<{ label: string; value: string }> = []
    if (v.gender) items.push({ label: 'Gender', value: genderLabel(v.gender) })
    if (v.descriptive) items.push({ label: 'Style', value: v.descriptive })
    if (v.accent) items.push({ label: 'Accent', value: v.accent })
    if (v.age) items.push({ label: 'Age', value: v.age })
    return items
  })

  return (
    <button
      type="button"
      onClick={() => {
        props.onSelect()
      }}
      class={`arcane-card-sm p-4 text-left w-full transition-colors cursor-pointer ${
        props.isSelected ? 'ring-2 ring-accent bg-accent/10' : 'hover:bg-surface-hover'
      }`}
    >
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0 flex-1">
          <p class="font-semibold text-foreground truncate">
            {props.voice.name ?? props.voice.external_id ?? `Voice #${String(props.voice.id)}`}
          </p>
          <div class="flex flex-wrap gap-1.5 mt-1.5">
            <For each={attrs()}>
              {(attr) => (
                <Badge variant="outline">
                  <span class="text-muted mr-1">{attr.label}:</span> {attr.value}
                </Badge>
              )}
            </For>
          </div>
        </div>
        <button
          type="button"
          class="shrink-0 text-xs px-2 py-1 rounded bg-surface hover:bg-accent/20 text-accent transition-colors"
          onClick={(e) => {
            e.stopPropagation()
            props.onPreview()
          }}
          disabled={props.isPreviewing}
        >
          {props.isPreviewing ? '...' : '▶ Preview'}
        </button>
      </div>
    </button>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const ProfessorVoice: Component = () => {
  const params = useParams<{ id: string }>()
  const professorId = createMemo(() => {
    const id = Number.parseInt(params.id, 10)
    return Number.isNaN(id) ? null : id
  })

  // ---- Professor + current voice ----
  const [professor, { refetch: refetchProfessor }] = createResource(
    () => professorId(),
    async (id) => professorService.getProfessor(id)
  )

  const [currentVoice] = createResource(
    () => {
      const p = professor()
      return p && typeof p.voice_id === 'number' ? p.voice_id : null
    },
    async (voiceId) => (voiceId ? getVoice(voiceId) : undefined)
  )

  // ---- Backend selection ----
  const [selectedBackend, setSelectedBackend] = createSignal<TtsBackendKey>('mistral')

  // ---- ElevenLabs manual ID ----
  const [elVoiceId, setElVoiceId] = createSignal('')

  // ---- Voices list for current backend ----
  const [voicesResource] = createResource(
    () => selectedBackend(),
    async (backend) => listVoices({ tts_backend: backend, limit: 100 })
  )

  // ---- Selected voice from grid ----
  const [selectedVoiceId, setSelectedVoiceId] = createSignal<number | null>(null)
  const selectedVoice = createMemo(() => {
    const id = selectedVoiceId()
    if (id === null) return null
    return voicesResource()?.items.find((v) => v.id === id) ?? null
  })

  // ---- Audio preview ----
  const [previewAudioUri, setPreviewAudioUri] = createSignal<string | null>(null)
  const [isPreviewingId, setIsPreviewingId] = createSignal<number | null>(null)

  const handlePreview = async (voice: Voice) => {
    const externalId = voice.external_id ?? voice.el_voice_id
    if (!externalId) return
    setIsPreviewingId(voice.id)
    setPreviewAudioUri(null)
    try {
      const resp = await previewVoice({
        voice_id: externalId,
        tts_backend: voice.tts_backend,
      })
      setPreviewAudioUri(resp.audio_data_uri)
    } catch (e) {
      console.error('Preview failed', e)
    } finally {
      setIsPreviewingId(null)
    }
  }

  // ---- Assignment ----
  const [isAssigning, setIsAssigning] = createSignal(false)
  const [assignError, setAssignError] = createSignal('')
  const [assignSuccess, setAssignSuccess] = createSignal('')

  const handleAssign = async () => {
    const pId = professorId()
    if (!pId) return

    setAssignError('')
    setAssignSuccess('')

    const backend = selectedBackend()
    let externalId: string | undefined
    let ttsBackend: string | undefined

    if (backend === 'elevenlabs') {
      const id = elVoiceId().trim()
      if (!id) {
        setAssignError('Please enter an ElevenLabs voice ID.')
        return
      }
      externalId = id
      ttsBackend = 'elevenlabs'
    } else {
      const voice = selectedVoice()
      if (!voice) {
        setAssignError('Please select a voice first.')
        return
      }
      externalId = voice.external_id ?? undefined
      ttsBackend = voice.tts_backend
    }

    if (!externalId) {
      setAssignError('No voice identifier found.')
      return
    }

    setIsAssigning(true)
    try {
      await manualAssignVoice(String(pId), {
        external_id: externalId,
        tts_backend: ttsBackend,
      })
      setAssignSuccess(`Voice assigned successfully (${ttsBackend}: ${externalId}).`)
      void refetchProfessor()
    } catch (e) {
      setAssignError(e instanceof Error ? e.message : 'Assignment failed.')
    } finally {
      setIsAssigning(false)
    }
  }

  // Reset selection when backend changes
  const switchBackend = (b: TtsBackendKey) => {
    setSelectedBackend(b)
    setSelectedVoiceId(null)
    setPreviewAudioUri(null)
    setAssignError('')
    setAssignSuccess('')
  }

  return (
    <div class="space-y-6">
      {/* Header */}
      <div>
        <Show when={professor()} fallback={<LoadingSpinner />}>
          {(prof) => (
            <h1 class="text-3xl font-display text-parchment-100 text-shadow-golden">
              Voice Selection — {prof().name}
            </h1>
          )}
        </Show>
      </div>

      {/* Current voice summary */}
      <Show when={professor()?.voice_id}>
        <div class="arcane-card p-4">
          <h2 class="text-lg font-display text-parchment-100 mb-2">Current Voice</h2>
          <Show when={currentVoice()} fallback={<p class="text-muted text-sm">Loading...</p>}>
            {(voice) => (
              <div class="flex flex-wrap items-center gap-2 text-sm">
                <Badge variant="secondary">
                  {voice().tts_backend === 'elevenlabs' ? 'ElevenLabs' : 'Voxtral'}
                </Badge>
                <span class="text-foreground font-medium">
                  {voice().name ?? voice().external_id ?? voice().el_voice_id}
                </span>
                <Show when={voice().gender}>
                  <Badge variant="outline">{genderLabel(voice().gender)}</Badge>
                </Show>
                <Show when={voice().descriptive}>
                  <Badge variant="outline">{voice().descriptive}</Badge>
                </Show>
              </div>
            )}
          </Show>
        </div>
      </Show>

      <RequireRole minRole="creator">
        {/* Backend selector tabs */}
        <div class="flex gap-2">
          <For each={BACKEND_OPTIONS}>
            {(opt) => (
              <button
                type="button"
                class={`px-4 py-2 rounded-t font-medium text-sm transition-colors ${
                  selectedBackend() === opt.value
                    ? 'bg-surface text-accent border-b-2 border-accent'
                    : 'bg-transparent text-muted hover:text-foreground'
                }`}
                onClick={() => {
                  switchBackend(opt.value)
                }}
              >
                {opt.label}
              </button>
            )}
          </For>
        </div>

        <div class="arcane-card p-5">
          {/* ElevenLabs: simple paste-ID form */}
          <Show when={selectedBackend() === 'elevenlabs'}>
            <div class="space-y-4">
              <p class="text-sm text-muted">
                Paste an existing ElevenLabs voice ID to assign it to this professor.
              </p>
              <div class="flex items-center gap-3">
                <input
                  type="text"
                  class="arcane-input flex-1"
                  placeholder="e.g. pNInz6obpgDQGcFmaJgB"
                  value={elVoiceId()}
                  onInput={(e) => setElVoiceId((e.target as HTMLInputElement).value)}
                  aria-label="ElevenLabs Voice ID"
                />
                <Button
                  variant="primary"
                  onClick={() => void handleAssign()}
                  disabled={!elVoiceId().trim() || isAssigning()}
                >
                  {isAssigning() ? 'Assigning...' : 'Assign'}
                </Button>
              </div>
            </div>
          </Show>

          {/* Mistral: voice browsing grid */}
          <Show when={selectedBackend() === 'mistral'}>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <p class="text-sm text-muted">
                  Browse Voxtral preset voices and preview them before assigning.
                </p>
                <Show when={selectedVoice()}>
                  <Button
                    variant="primary"
                    onClick={() => void handleAssign()}
                    disabled={isAssigning()}
                  >
                    {isAssigning()
                      ? 'Assigning...'
                      : `Assign "${selectedVoice()?.name ?? 'voice'}"`}
                  </Button>
                </Show>
              </div>

              <Show when={!voicesResource.loading} fallback={<LoadingSpinner />}>
                <Show
                  when={(voicesResource()?.items.length ?? 0) > 0}
                  fallback={
                    <p class="text-muted text-sm">
                      No Mistral voices found in the database. Run the seed script first:
                      <code class="ml-1 text-accent">
                        hatch run python scripts/seed_mistral_voices.py
                      </code>
                    </p>
                  }
                >
                  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <For each={voicesResource()?.items ?? []}>
                      {(voice) => (
                        <VoiceCard
                          voice={voice}
                          isSelected={selectedVoiceId() === voice.id}
                          isPreviewing={isPreviewingId() === voice.id}
                          onSelect={() => setSelectedVoiceId(voice.id)}
                          onPreview={() => {
                            void handlePreview(voice)
                          }}
                        />
                      )}
                    </For>
                  </div>
                </Show>
              </Show>

              {/* Audio player for preview */}
              <Show when={previewAudioUri()}>
                <div class="mt-4 p-3 bg-surface rounded-lg">
                  <p class="text-xs text-muted mb-2">Voice Preview</p>
                  <audio
                    controls
                    autoplay
                    class="w-full max-w-md"
                    src={previewAudioUri() ?? ''}
                    aria-label="Voice preview audio"
                  >
                    <track
                      kind="captions"
                      src="data:text/vtt;charset=utf-8,WEBVTT%0A%0A"
                      srclang="en"
                      label="English captions"
                      default
                    />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              </Show>
            </div>
          </Show>

          {/* Status messages */}
          <Show when={assignError()}>
            <Alert variant="danger" class="mt-4">
              {assignError()}
            </Alert>
          </Show>
          <Show when={assignSuccess()}>
            <Alert variant="success" class="mt-4">
              {assignSuccess()}
            </Alert>
          </Show>
        </div>
      </RequireRole>
    </div>
  )
}

export default ProfessorVoice
