import { useParams } from '@solidjs/router'
import {
  type Component,
  createEffect,
  createMemo,
  createResource,
  createSignal,
  For,
  Show,
} from 'solid-js'
import { professorService } from '../../api/services/professor-service.js'
import {
  cloneVoiceToMistral,
  generateVoiceDesignPreviews,
  getVoice,
  listMistralCatalog,
  listXaiCatalog,
  manualAssignVoice,
  previewVoice,
  saveDesignedVoice,
} from '../../api/services/voice-service.js'
import type { MistralCatalogVoice, VoiceDesignPreview, XaiCatalogVoice } from '../../api/types.js'
import { RequireRole } from '../../auth/RequireRole'
import { Alert, Badge, Button, LoadingSpinner } from '../ui'

type TtsBackendKey = 'elevenlabs' | 'mistral' | 'xai'

const BACKEND_OPTIONS: Array<{ value: TtsBackendKey; label: string }> = [
  { value: 'elevenlabs', label: 'ElevenLabs' },
  { value: 'mistral', label: 'Voxtral (Mistral)' },
  { value: 'xai', label: 'xAI (Grok)' },
]

/** Display-friendly name for a TTS backend. */
const backendLabel = (backend: string | null | undefined): string => {
  const map: Record<string, string> = {
    elevenlabs: 'ElevenLabs',
    mistral: 'Voxtral',
    xai: 'xAI (Grok)',
  }
  return (backend && map[backend]) ?? 'ElevenLabs'
}

const EXCLUDED_MISTRAL_EMOTIONS = new Set(['sad', 'angry', 'shameful', 'jealousy', 'frustrated'])

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
  voice: MistralCatalogVoice
  isSelected: boolean
  isPreviewing: boolean
  onSelect: () => void
  onPreview: () => void
}> = (props) => {
  const attrs = createMemo(() => {
    const v = props.voice
    const items: Array<{ label: string; value: string }> = []
    if (v.gender) items.push({ label: 'Gender', value: genderLabel(v.gender) })
    if (v.tags?.length) {
      const emotion = v.tags[v.tags.length - 1]
      if (emotion) items.push({ label: 'Style', value: emotion })
    }
    if (v.languages?.length) {
      items.push({ label: 'Lang', value: v.languages.join(', ') })
    }
    return items
  })

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => {
        props.onSelect()
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          props.onSelect()
        }
      }}
      class={`arcane-card-sm p-4 text-left w-full transition-colors cursor-pointer ${
        props.isSelected ? 'ring-2 ring-accent bg-accent/10' : 'hover:bg-surface-hover'
      }`}
    >
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0 flex-1">
          <p class="font-semibold text-foreground truncate">{props.voice.name}</p>
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
    </div>
  )
}

// ---------------------------------------------------------------------------
// Voice card for xAI voices (DB-backed Voice records)
// ---------------------------------------------------------------------------
const XaiVoiceCard: Component<{
  voice: XaiCatalogVoice
  isSelected: boolean
  isPreviewing: boolean
  onSelect: () => void
  onPreview: () => void
}> = (props) => {
  const attrs = createMemo(() => {
    const v = props.voice
    const items: Array<{ label: string; value: string }> = []
    if (v.gender) items.push({ label: 'Gender', value: genderLabel(v.gender) })
    if (v.language) items.push({ label: 'Lang', value: v.language })
    return items
  })

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => {
        props.onSelect()
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          props.onSelect()
        }
      }}
      class={`arcane-card-sm p-4 text-left w-full transition-colors cursor-pointer ${
        props.isSelected ? 'ring-2 ring-accent bg-accent/10' : 'hover:bg-surface-hover'
      }`}
    >
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0 flex-1">
          <p class="font-semibold text-foreground truncate">{props.voice.name}</p>
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
    </div>
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
  // Default to the current voice's backend once it loads; fall back to 'elevenlabs'
  const [selectedBackend, setSelectedBackend] = createSignal<TtsBackendKey>('elevenlabs')
  let backendInitialized = false
  createEffect(() => {
    const voice = currentVoice()
    if (!backendInitialized && voice) {
      backendInitialized = true
      const backend = voice.tts_backend
      if (backend === 'mistral' || backend === 'xai') {
        setSelectedBackend(backend)
      } else {
        setSelectedBackend('elevenlabs')
      }
    }
  })

  // ---- ElevenLabs manual ID ----
  const [elVoiceId, setElVoiceId] = createSignal('')

  // ---- Mistral catalog (on-demand from Mistral API) ----
  const [showAllMistralEmotions, setShowAllMistralEmotions] = createSignal(false)
  const [mistralCatalog] = createResource(
    () => (selectedBackend() === 'mistral' ? true : null),
    async (enabled) => (enabled ? listMistralCatalog() : undefined)
  )
  const filteredMistralVoices = createMemo(() => {
    const items = mistralCatalog()?.items ?? []
    if (showAllMistralEmotions()) return items
    return items.filter((v) => {
      const tags = v.tags ?? []
      return !tags.some((t) => EXCLUDED_MISTRAL_EMOTIONS.has(t.toLowerCase()))
    })
  })

  // ---- Selected Mistral voice (by UUID string) ----
  const [selectedMistralId, setSelectedMistralId] = createSignal<string | null>(null)
  const selectedMistralVoice = createMemo(() => {
    const id = selectedMistralId()
    if (!id) return null
    return mistralCatalog()?.items.find((v) => v.id === id) ?? null
  })

  // ---- xAI voices (on-demand from the xAI API; read fresh each time) ----
  const [xaiCatalog] = createResource(
    () => (selectedBackend() === 'xai' ? true : null),
    async (enabled) => (enabled ? listXaiCatalog() : undefined)
  )
  const [selectedXaiId, setSelectedXaiId] = createSignal<string | null>(null)
  const selectedXaiVoice = createMemo(() => {
    const id = selectedXaiId()
    if (!id) return null
    return xaiCatalog()?.items.find((v) => v.id === id) ?? null
  })

  // ---- Audio preview ----
  const [previewAudioUri, setPreviewAudioUri] = createSignal<string | null>(null)
  const [isPreviewingId, setIsPreviewingId] = createSignal<string | null>(null)

  const handlePreview = async (voice: MistralCatalogVoice) => {
    setIsPreviewingId(voice.id)
    setPreviewAudioUri(null)
    try {
      const resp = await previewVoice({
        voice_id: voice.id,
        tts_backend: 'mistral',
      })
      setPreviewAudioUri(resp.audio_data_uri)
    } catch (e) {
      console.error('Preview failed', e)
    } finally {
      setIsPreviewingId(null)
    }
  }

  const handleXaiPreview = async (voice: XaiCatalogVoice) => {
    setIsPreviewingId(voice.id)
    setPreviewAudioUri(null)
    try {
      const resp = await previewVoice({
        voice_id: voice.id,
        tts_backend: 'xai',
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
  const [isReassigning, setIsReassigning] = createSignal(false)
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
    } else if (backend === 'xai') {
      const voice = selectedXaiVoice()
      if (!voice) {
        setAssignError('Please select a voice first.')
        return
      }
      externalId = voice.id
      ttsBackend = 'xai'
    } else {
      const voice = selectedMistralVoice()
      if (!voice) {
        setAssignError('Please select a voice first.')
        return
      }
      externalId = voice.id
      ttsBackend = 'mistral'
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

  const handleReassignVoice = async () => {
    const pId = professorId()
    if (!pId) return
    setAssignError('')
    setAssignSuccess('')
    setIsReassigning(true)
    try {
      await professorService.assignVoiceToProfessor(pId)
      setAssignSuccess('Voice reassigned successfully.')
      void refetchProfessor()
    } catch (e) {
      setAssignError(e instanceof Error ? e.message : 'Reassignment failed.')
    } finally {
      setIsReassigning(false)
    }
  }

  // ---- Current Mistral voice preview ----
  const [currentMistralPreviewUri, setCurrentMistralPreviewUri] = createSignal<string | null>(null)
  const [isPreviewingCurrentVoice, setIsPreviewingCurrentVoice] = createSignal(false)

  const handlePreviewCurrentVoice = async () => {
    const voice = currentVoice()
    if (!voice?.external_id) return
    setIsPreviewingCurrentVoice(true)
    setCurrentMistralPreviewUri(null)
    try {
      const resp = await previewVoice({ voice_id: voice.external_id, tts_backend: 'mistral' })
      setCurrentMistralPreviewUri(resp.audio_data_uri)
    } catch (e) {
      console.error('Current voice preview failed', e)
    } finally {
      setIsPreviewingCurrentVoice(false)
    }
  }

  // ---- Clone to Mistral ----
  const [isCloningToMistral, setIsCloningToMistral] = createSignal(false)
  const [cloneError, setCloneError] = createSignal('')

  const handleCloneToMistral = async () => {
    const pId = professorId()
    if (!pId) return
    setCloneError('')
    setAssignError('')
    setAssignSuccess('')
    setIsCloningToMistral(true)
    try {
      await cloneVoiceToMistral({ professor_id: pId })
      setAssignSuccess('Voice cloned to Mistral successfully.')
      void refetchProfessor()
    } catch (e) {
      setCloneError(e instanceof Error ? e.message : 'Cloning failed.')
    } finally {
      setIsCloningToMistral(false)
    }
  }

  // ---- Voice Design ----
  const [designPreviews, setDesignPreviews] = createSignal<VoiceDesignPreview[]>([])
  const [isGeneratingPreviews, setIsGeneratingPreviews] = createSignal(false)
  const [designError, setDesignError] = createSignal('')
  // Per-preview name inputs (keyed by generated_voice_id)
  const [previewNames, setPreviewNames] = createSignal<Record<string, string>>({})
  const [isSavingId, setIsSavingId] = createSignal<string | null>(null)

  const handleGeneratePreviews = async () => {
    const pId = professorId()
    if (!pId) return
    setDesignError('')
    setDesignPreviews([])
    setPreviewNames({})
    setIsGeneratingPreviews(true)
    try {
      const result = await generateVoiceDesignPreviews(pId)
      setDesignPreviews(result.previews)
      // Seed default names: "Prof. Name — Voice 1", etc.
      const profName = professor()?.name ?? 'Professor'
      const names: Record<string, string> = {}
      result.previews.forEach((p, i) => {
        names[p.generated_voice_id] = `${profName} — Voice ${String(i + 1)}`
      })
      setPreviewNames(names)
    } catch (e) {
      setDesignError(e instanceof Error ? e.message : 'Failed to generate voice previews.')
    } finally {
      setIsGeneratingPreviews(false)
    }
  }

  const handleSaveDesignedVoice = async (preview: VoiceDesignPreview) => {
    const pId = professorId()
    if (!pId) return
    setDesignError('')
    setIsSavingId(preview.generated_voice_id)
    try {
      await saveDesignedVoice({
        professor_id: pId,
        generated_voice_id: preview.generated_voice_id,
        voice_name: previewNames()[preview.generated_voice_id] ?? 'Generated Voice',
        voice_description: preview.voice_description,
      })
      setDesignPreviews([])
      setPreviewNames({})
      setAssignSuccess('New voice saved and assigned successfully.')
      void refetchProfessor()
    } catch (e) {
      setDesignError(e instanceof Error ? e.message : 'Failed to save voice.')
    } finally {
      setIsSavingId(null)
    }
  }

  // Reset selection when backend changes
  const switchBackend = (b: TtsBackendKey) => {
    setSelectedBackend(b)
    setSelectedMistralId(null)
    setSelectedXaiId(null)
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
        <div class="arcane-card p-4 space-y-3">
          <h2 class="text-lg font-display text-parchment-100">Current Voice</h2>
          <Show when={currentVoice()} fallback={<p class="text-muted text-sm">Loading...</p>}>
            {(voice) => (
              <>
                <div class="flex flex-wrap items-center gap-2 text-sm">
                  <Badge variant="secondary">{backendLabel(voice().tts_backend)}</Badge>
                  <span class="text-foreground font-medium">
                    {voice().name ?? voice().external_id ?? voice().el_voice_id}
                  </span>
                  <Show when={voice().gender}>
                    <Badge variant="outline">{genderLabel(voice().gender)}</Badge>
                  </Show>
                  <Show when={voice().descriptive}>
                    <Badge variant="outline">{voice().descriptive}</Badge>
                  </Show>
                  <Show when={voice().tts_backend === 'mistral' && voice().external_id}>
                    <button
                      type="button"
                      class="text-xs px-2 py-1 rounded bg-surface hover:bg-accent/20 text-accent transition-colors disabled:opacity-50"
                      onClick={() => void handlePreviewCurrentVoice()}
                      disabled={isPreviewingCurrentVoice()}
                    >
                      {isPreviewingCurrentVoice() ? '…' : '▶ Preview'}
                    </button>
                  </Show>
                </div>
                <Show when={currentMistralPreviewUri()}>
                  <audio
                    controls
                    autoplay
                    class="w-full max-w-sm"
                    src={currentMistralPreviewUri() ?? ''}
                    aria-label="Current voice preview"
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
                </Show>
              </>
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
            <div class="space-y-6">
              {/* Preview for the currently assigned ElevenLabs voice */}
              <Show
                when={currentVoice()?.tts_backend === 'elevenlabs' && currentVoice()?.preview_url}
              >
                <div class="space-y-2">
                  <p class="text-sm font-medium text-foreground">Current voice preview</p>
                  <audio
                    controls
                    class="w-full max-w-sm"
                    aria-label="Current voice preview"
                    src={currentVoice()?.preview_url ?? ''}
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
                    onInput={(e: InputEvent & { currentTarget: HTMLInputElement }) =>
                      setElVoiceId(e.currentTarget.value)
                    }
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

              <div class="border-t border-parchment-800/30 pt-5 space-y-3">
                <div>
                  <p class="text-sm font-medium text-foreground">Try another voice</p>
                  <p class="text-xs text-muted mt-0.5">
                    Automatically pick a matching ElevenLabs voice based on this professor's
                    attributes (gender, accent, age).
                  </p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => void handleReassignVoice()}
                  disabled={isReassigning()}
                >
                  {isReassigning() ? 'Reassigning...' : 'Reassign Voice'}
                </Button>
              </div>

              {/* Voice Design — experimental */}
              <div class="border-t border-parchment-800/30 pt-5 space-y-4">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="text-sm font-medium text-foreground">
                      Generate a New Voice{' '}
                      <span class="text-xs font-normal text-accent ml-1">[Experimental]</span>
                    </p>
                    <p class="text-xs text-muted mt-0.5">
                      Create a custom ElevenLabs voice from this professor's attributes. Listen to
                      the options and choose your favourite.
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() => void handleGeneratePreviews()}
                    disabled={isGeneratingPreviews()}
                    class="shrink-0"
                  >
                    {isGeneratingPreviews() ? (
                      <span class="flex items-center gap-2">
                        <LoadingSpinner size="sm" />
                        Generating…
                      </span>
                    ) : (
                      'Generate Options'
                    )}
                  </Button>
                </div>

                <Show when={designError()}>
                  <Alert variant="danger">{designError()}</Alert>
                </Show>

                <Show when={designPreviews().length > 0}>
                  <div class="space-y-3">
                    <For each={designPreviews()}>
                      {(preview, i) => (
                        <div class="arcane-card-sm p-4 space-y-3">
                          <div class="flex items-center justify-between gap-3">
                            <input
                              type="text"
                              class="arcane-input flex-1 text-sm"
                              value={
                                previewNames()[preview.generated_voice_id] ??
                                `Voice ${String(i() + 1)}`
                              }
                              onInput={(e: InputEvent & { currentTarget: HTMLInputElement }) =>
                                setPreviewNames((prev) => ({
                                  ...prev,
                                  [preview.generated_voice_id]: e.currentTarget.value,
                                }))
                              }
                              aria-label={`Name for voice option ${String(i() + 1)}`}
                            />
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => void handleSaveDesignedVoice(preview)}
                              disabled={isSavingId() !== null}
                              class="shrink-0"
                            >
                              {isSavingId() === preview.generated_voice_id
                                ? 'Saving…'
                                : 'Use This Voice'}
                            </Button>
                          </div>
                          <audio
                            controls
                            class="w-full max-w-md"
                            src={`data:${preview.media_type};base64,${preview.audio_sample}`}
                            aria-label={`Preview for voice option ${String(i() + 1)}`}
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
                      )}
                    </For>
                  </div>
                </Show>
              </div>

              {/* Clone to Mistral */}
              <Show
                when={currentVoice()?.tts_backend === 'elevenlabs' && currentVoice()?.preview_url}
              >
                <div class="border-t border-parchment-800/30 pt-5 flex flex-col gap-2">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="text-sm font-medium text-foreground">Clone to Mistral</p>
                      <p class="text-xs text-muted mt-0.5">
                        Clone this voice into your Mistral library and switch the professor to
                        Voxtral TTS.
                      </p>
                    </div>
                    <Button
                      variant="secondary"
                      onClick={() => void handleCloneToMistral()}
                      disabled={isCloningToMistral()}
                      class="shrink-0"
                    >
                      {isCloningToMistral() ? 'Cloning…' : 'Clone to Mistral'}
                    </Button>
                  </div>
                  <Show when={cloneError()}>
                    <Alert variant="danger" class="text-sm">
                      {cloneError()}
                    </Alert>
                  </Show>
                </div>
              </Show>
            </div>
          </Show>

          {/* Mistral: voice browsing grid (on-demand from Mistral API) */}
          <Show when={selectedBackend() === 'mistral'}>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <p class="text-sm text-muted">
                  Browse Voxtral voices and preview them before assigning.
                </p>
                <Show when={selectedMistralVoice()}>
                  <Button
                    variant="primary"
                    onClick={() => void handleAssign()}
                    disabled={isAssigning()}
                  >
                    {isAssigning()
                      ? 'Assigning...'
                      : `Assign "${selectedMistralVoice()?.name ?? 'voice'}"`}
                  </Button>
                </Show>
              </div>

              <Show when={!mistralCatalog.loading} fallback={<LoadingSpinner />}>
                <Show
                  when={filteredMistralVoices().length > 0}
                  fallback={
                    <p class="text-muted text-sm">
                      No Mistral voices found. Check that MISTRAL_API_KEY is configured.
                    </p>
                  }
                >
                  <label class="flex items-center gap-2 text-xs text-muted">
                    <input
                      type="checkbox"
                      checked={showAllMistralEmotions()}
                      onChange={(e: Event & { currentTarget: HTMLInputElement }) =>
                        setShowAllMistralEmotions(e.currentTarget.checked)
                      }
                    />
                    Show all emotional tones (including sad/angry/frustrated/etc.)
                  </label>
                  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <For each={filteredMistralVoices()}>
                      {(voice) => (
                        <VoiceCard
                          voice={voice}
                          isSelected={selectedMistralId() === voice.id}
                          isPreviewing={isPreviewingId() === voice.id}
                          onSelect={() => setSelectedMistralId(voice.id)}
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

          {/* xAI: voice browsing grid (DB-backed; seeded voices) */}
          <Show when={selectedBackend() === 'xai'}>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <p class="text-sm text-muted">
                  Browse xAI (Grok) voices and preview them before assigning.
                </p>
                <Show when={selectedXaiVoice()}>
                  <Button
                    variant="primary"
                    onClick={() => void handleAssign()}
                    disabled={isAssigning()}
                  >
                    {isAssigning()
                      ? 'Assigning...'
                      : `Assign "${selectedXaiVoice()?.name ?? 'voice'}"`}
                  </Button>
                </Show>
              </div>

              <Show when={!xaiCatalog.loading} fallback={<LoadingSpinner />}>
                <Show
                  when={(xaiCatalog()?.items.length ?? 0) > 0}
                  fallback={
                    <p class="text-muted text-sm">
                      No xAI voices found. Check that XAI_API_KEY is configured.
                    </p>
                  }
                >
                  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <For each={xaiCatalog()?.items ?? []}>
                      {(voice) => (
                        <XaiVoiceCard
                          voice={voice}
                          isSelected={selectedXaiId() === voice.id}
                          isPreviewing={isPreviewingId() === voice.id}
                          onSelect={() => setSelectedXaiId(voice.id)}
                          onPreview={() => {
                            void handleXaiPreview(voice)
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
