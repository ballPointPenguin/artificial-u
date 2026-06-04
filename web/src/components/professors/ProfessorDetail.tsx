import { A, useNavigate, useParams } from '@solidjs/router'
import { type Component, createResource, createSignal, For, type Resource, Show } from 'solid-js'
import { departmentService } from '../../api/services/department-service.js'
import { professorService } from '../../api/services/professor-service.js'
import { getVoice } from '../../api/services/voice-service.js'
import type {
  Professor,
  ProfessorCourseBrief,
  ProfessorCoursesResponse,
  Voice,
} from '../../api/types.js'
import { useAuth } from '../../auth/AuthProvider'
import { RequireRole } from '../../auth/RequireRole'
import { Alert, Button, ConfirmationModal, LoadingSpinner, MagicButton, MetadataInfo } from '../ui'
import ProfessorForm, { type ProfessorFormData } from './ProfessorForm.js'

// Professor Courses Component
const ProfessorCourses: Component<{
  coursesResource: () => ProfessorCoursesResponse | undefined
  loading: boolean
  error: unknown
}> = (props) => {
  const courses = () => props.coursesResource()?.courses
  return (
    <div class="mt-8">
      <h2 class="text-2xl font-display text-parchment-100 mb-4 text-shadow-golden">
        Courses Taught
      </h2>
      <Show when={!props.loading} fallback={<p class="text-muted">Loading courses...</p>}>
        <Show
          when={!props.error}
          fallback={
            <Alert variant="danger">
              Error loading courses:{' '}
              {props.error instanceof Error ? props.error.message : 'Unknown error'}
            </Alert>
          }
        >
          <Show
            when={Array.isArray(courses()) && (courses()?.length ?? 0) > 0}
            fallback={
              <p class="text-muted">This professor is not currently teaching any courses.</p>
            }
          >
            <ul class="space-y-2">
              <For each={courses() ?? []}>
                {(course: ProfessorCourseBrief) => (
                  <li class="arcane-card-sm p-3">
                    <A href={`/courses/${String(course.id)}`} class="hover:text-primary">
                      <strong class="font-semibold text-foreground">{course.code}:</strong>{' '}
                      {course.title}
                    </A>
                    <div class="text-xs text-muted mt-1">
                      <span>Level: {course.level}</span>
                    </div>
                  </li>
                )}
              </For>
            </ul>
          </Show>
        </Show>
      </Show>
    </div>
  )
}

/** Display name for a TTS backend key. */
const backendDisplayName = (backend: string): string => {
  const names: Record<string, string> = {
    elevenlabs: 'ElevenLabs',
    mistral: 'Mistral',
    xai: 'xAI (Grok)',
  }
  return names[backend] ?? backend
}

/** Reusable voice profile section used in both desktop and mobile layouts. */
const VoiceProfileSection: Component<{
  professorResource: Resource<Professor | undefined>
  voiceResource: Resource<Voice | undefined>
}> = (props) => {
  /** Optional voice attributes shown only when non-empty. */
  const optionalAttrs = (): Array<{ label: string; value: string }> => {
    const voice = props.voiceResource()
    if (!voice) return []
    const candidates: Array<{ label: string; value: string | null | undefined }> = [
      { label: 'Accent', value: voice.accent },
      { label: 'Gender', value: voice.gender },
      { label: 'Age', value: voice.age },
      { label: 'Descriptive', value: voice.descriptive },
      { label: 'Use Case', value: voice.use_case },
    ]
    return candidates.filter((a): a is { label: string; value: string } => Boolean(a.value))
  }

  return (
    <>
      <h3 class="text-lg font-display text-parchment-100 mb-3 text-shadow-golden">Voice Profile</h3>
      <div class="bg-surface rounded-lg p-4 space-y-2">
        <Show when={props.professorResource()?.voice_id}>
          <Show when={!props.voiceResource.loading && props.voiceResource()}>
            {(voice) => (
              <>
                {/* TTS Backend badge */}
                <p class="text-sm text-muted">
                  <strong class="font-semibold text-foreground">Backend:</strong>{' '}
                  <span class="inline-block px-2 py-0.5 rounded text-xs font-medium bg-accent/20 text-accent">
                    {backendDisplayName(voice().tts_backend)}
                  </span>
                </p>

                {/* Voice name — always shown when present */}
                <Show when={voice().name}>
                  <p class="text-sm text-muted">
                    <strong class="font-semibold text-foreground">Name:</strong> {voice().name}
                  </p>
                </Show>

                {/* ElevenLabs link — only for elevenlabs backend */}
                <Show when={voice().tts_backend === 'elevenlabs' && voice().el_voice_id}>
                  <p class="text-sm text-muted">
                    <strong class="font-semibold text-foreground">ElevenLabs ID:</strong>{' '}
                    <a
                      href={`https://elevenlabs.io/app/voice-library?voiceId=${voice().el_voice_id ?? ''}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-accent hover:text-accent/80 underline"
                    >
                      {voice().el_voice_id}
                    </a>
                  </p>
                </Show>

                {/* Optional attributes — rendered dynamically */}
                <For each={optionalAttrs()}>
                  {(attr) => (
                    <p class="text-sm text-muted">
                      <strong class="font-semibold text-foreground">{attr.label}:</strong>{' '}
                      {attr.value}
                    </p>
                  )}
                </For>

                {/* Audio preview — backend-agnostic */}
                <Show when={voice().preview_url}>
                  <div class="mt-3">
                    <audio controls class="w-full max-w-sm" aria-label="Voice preview">
                      <source src={voice().preview_url ?? ''} type="audio/mpeg" />
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
              </>
            )}
          </Show>

          <Show when={props.voiceResource.loading}>
            <p class="text-sm text-muted italic">Loading voice details...</p>
          </Show>

          <Show when={props.voiceResource.error as unknown}>
            <p class="text-sm text-danger">
              Error loading voice details:{' '}
              {props.voiceResource.error instanceof Error
                ? props.voiceResource.error.message
                : 'Unknown error'}
            </p>
          </Show>
        </Show>

        {/* Link to Voice Selection page */}
        <Show when={props.professorResource()?.id}>
          <RequireRole minRole="creator">
            <div class="mt-3">
              <A
                href={`/professors/${String(props.professorResource()?.id ?? '')}/voice`}
                class="text-sm text-accent hover:text-accent/80 underline"
              >
                Voice Selection &amp; Preview &rarr;
              </A>
            </div>
          </RequireRole>
        </Show>
      </div>
    </>
  )
}

export default function ProfessorDetail() {
  const params = useParams()
  const navigate = useNavigate()
  const auth = useAuth()
  const [isEditing, setIsEditing] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')
  const [isGeneratingImage, setIsGeneratingImage] = createSignal(false)
  const [generationError, setGenerationError] = createSignal('')
  const [isImageLoading, setIsImageLoading] = createSignal(false)
  const [professorResource, { refetch: refetchProfessor }] = createResource(
    () => {
      const id = Number.parseInt(params.id ?? '', 10)
      if (Number.isNaN(id)) {
        throw new Error('Professor ID is missing or invalid')
      }
      return id
    },
    async (id) => {
      setIsImageLoading(false) // Reset image loading state when professor data changes
      return professorService.getProfessor(id)
    }
  )

  const [departmentResource] = createResource(
    () => {
      const prof = professorResource()
      return prof && typeof prof.department_id === 'number' ? prof.department_id : null
    },
    async (departmentId) => {
      return departmentService.getDepartment(departmentId)
    }
  )

  const [coursesResource] = createResource(
    () => professorResource()?.id,
    async (professorId: number) => {
      if (professorId) {
        return professorService.getProfessorCourses(professorId)
      }
      return undefined
    }
  )

  const [voiceResource] = createResource(
    () => {
      const prof = professorResource()
      return prof && typeof prof.voice_id === 'number' ? prof.voice_id : null
    },
    async (voiceId) => {
      if (voiceId) {
        return getVoice(voiceId)
      }
      return undefined
    }
  )

  const getErrorMessage = (resourceError: unknown) => {
    return resourceError instanceof Error ? resourceError.message : 'Unknown error'
  }

  const handleSubmitUpdate = async (formData: ProfessorFormData) => {
    setIsSubmitting(true)
    setError('')

    try {
      const id = Number.parseInt(params.id ?? '', 10)
      if (Number.isNaN(id)) {
        throw new Error('Invalid professor ID')
      }

      const updatedProfessor = {
        ...formData,
        background: formData.background || '',
        personality: formData.personality || '',
        teaching_style: formData.teaching_style || '',
      }

      await professorService.updateProfessor(id, updatedProfessor)
      setIsEditing(false)
      void refetchProfessor()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update professor')
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
        throw new Error('Invalid professor ID')
      }

      await professorService.deleteProfessor(id)
      navigate('/professors')
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to delete professor')
      setIsDeleting(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleGenerateImage = async () => {
    setIsGeneratingImage(true)
    setGenerationError('')
    setError('')
    setIsImageLoading(false) // Clear any existing image loading state

    try {
      const id = Number.parseInt(params.id ?? '', 10)
      if (Number.isNaN(id)) {
        throw new Error('Invalid professor ID')
      }

      await professorService.generateProfessorImage(id)
      void refetchProfessor()
    } catch (error) {
      setGenerationError(error instanceof Error ? error.message : 'Failed to generate image')
    } finally {
      setIsGeneratingImage(false)
    }
  }

  return (
    <div class="arcane-card p-8">
      <Show
        when={!professorResource.loading}
        fallback={<p class="text-muted">Loading professor details...</p>}
      >
        <Show
          when={!professorResource.error}
          fallback={
            <Alert variant="danger" class="mb-4">
              <p>Error loading professor: {getErrorMessage(professorResource.error)}</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => void refetchProfessor()}
                class="mt-2"
              >
                Try Again
              </Button>
            </Alert>
          }
        >
          <Show
            when={!isEditing()}
            fallback={
              <div>
                <RequireRole minRole="creator">
                  <h2 class="text-xl font-semibold mb-4">Edit Professor</h2>
                  <ProfessorForm
                    professor={professorResource()}
                    onSubmit={handleSubmitUpdate}
                    onCancel={() => setIsEditing(false)}
                    isSubmitting={isSubmitting()}
                    error={error()}
                  />
                </RequireRole>
              </div>
            }
          >
            <div>
              <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-6">
                <h1 class="text-3xl font-display text-parchment-100 text-shadow-golden">
                  {professorResource()?.name}
                </h1>
                <div class="flex flex-wrap gap-2 items-center sm:justify-end">
                  <Show when={auth.canModify(professorResource()?.created_by)}>
                    <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)}>
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsDeleting(true)}
                      class="text-danger border-danger hover:bg-danger-bg hover:text-foreground"
                    >
                      Delete
                    </Button>
                  </Show>
                </div>
              </div>

              <Show when={generationError()}>
                <Alert variant="danger" class="mb-4">
                  <p>Error generating image: {generationError()}</p>
                </Alert>
              </Show>

              {/* Start of responsive layout with image prioritized on mobile */}
              <div class="flex flex-col gap-8 md:flex-row md:gap-8 mb-6">
                {/* Left Column: All Attributes */}
                <div class="order-2 md:order-1 md:w-1/2 space-y-3 text-muted">
                  <p>
                    <strong class="font-semibold text-foreground">Title:</strong>{' '}
                    <span class="text-muted">{professorResource()?.title}</span>
                  </p>
                  <Show when={professorResource()?.department_id}>
                    <p>
                      <strong class="font-semibold text-foreground">Department:</strong>{' '}
                      <Show
                        when={!departmentResource.loading && departmentResource()}
                        fallback={<span class="text-muted italic">Loading department...</span>}
                      >
                        <Show
                          when={!departmentResource.error && departmentResource()}
                          fallback={<span class="text-danger">Error loading department</span>}
                        >
                          {(dept) => <span class="text-muted">{dept().name}</span>}
                        </Show>
                      </Show>
                    </p>
                  </Show>

                  <Show when={professorResource()?.specialization}>
                    {(specialization) => (
                      <p>
                        <strong class="font-semibold text-foreground">Specialization:</strong>{' '}
                        <span class="text-muted">{specialization()}</span>
                      </p>
                    )}
                  </Show>

                  <Show when={professorResource()?.gender}>
                    {(gender) => (
                      <p>
                        <strong class="font-semibold text-foreground">Gender:</strong>{' '}
                        <span class="text-muted">{gender()}</span>
                      </p>
                    )}
                  </Show>

                  <Show when={professorResource()?.accent}>
                    {(accent) => (
                      <p>
                        <strong class="font-semibold text-foreground">Accent:</strong>{' '}
                        <span class="text-muted">{accent()}</span>
                      </p>
                    )}
                  </Show>

                  <Show when={professorResource()?.age}>
                    {(age) => (
                      <p>
                        <strong class="font-semibold text-foreground">Age:</strong>{' '}
                        <span class="text-muted">{age()}</span>
                      </p>
                    )}
                  </Show>

                  {/* Metadata Section */}
                  <div class="pt-3 mt-3 border-t border-parchment-800/30">
                    <MetadataInfo
                      createdBy={professorResource()?.student}
                      createdWith={professorResource()?.created_with}
                      createdAt={professorResource()?.created_at}
                    />
                  </div>

                  {/* Moved longer attributes here */}
                  <Show when={professorResource()?.description}>
                    {(desc) => (
                      <p>
                        <strong class="font-semibold text-foreground">Description:</strong>
                        <span class="block mt-1 whitespace-pre-wrap text-muted">{desc()}</span>
                      </p>
                    )}
                  </Show>

                  <Show when={professorResource()?.background}>
                    {(bg) => (
                      <p>
                        <strong class="font-semibold text-foreground">Background:</strong>
                        <span class="block mt-1 whitespace-pre-wrap text-muted">{bg()}</span>
                      </p>
                    )}
                  </Show>

                  <Show when={professorResource()?.teaching_style}>
                    {(style) => (
                      <p>
                        <strong class="font-semibold text-foreground">Teaching Style:</strong>{' '}
                        <span class="block mt-1 whitespace-pre-wrap text-muted">{style()}</span>
                      </p>
                    )}
                  </Show>

                  <Show when={professorResource()?.personality}>
                    {(pers) => (
                      <p>
                        <strong class="font-semibold text-foreground">Personality:</strong>{' '}
                        <span class="block mt-1 whitespace-pre-wrap text-muted">{pers()}</span>
                      </p>
                    )}
                  </Show>
                </div>

                {/* Image Column */}
                <div class="order-1 md:order-2 md:w-1/2 flex flex-col items-center gap-4">
                  <div class="relative flex flex-col items-center justify-center w-full min-h-[200px] bg-surface rounded-lg p-4">
                    <Show
                      when={isGeneratingImage() || isImageLoading()}
                      fallback={
                        <Show when={professorResource()?.image_url}>
                          <img
                            src={professorResource()?.image_url ?? ''}
                            alt={`Professor ${professorResource()?.name || ''}`}
                            class="w-full max-w-sm h-auto rounded-lg shadow-lg object-contain"
                            onLoad={() => setIsImageLoading(false)}
                            onLoadStart={() => setIsImageLoading(true)}
                            onError={(e) => {
                              console.log(
                                'Image failed to load:',
                                (e.target as HTMLImageElement).src
                              )
                              setIsImageLoading(false)
                            }}
                          />
                        </Show>
                      }
                    >
                      <div class="flex flex-col items-center space-y-2">
                        <LoadingSpinner size="lg" />
                        <p class="text-sm text-muted">
                          {isGeneratingImage() ? 'Generating image...' : 'Loading image...'}
                        </p>
                      </div>
                    </Show>
                    <Show
                      when={
                        professorResource()?.image_url && professorResource()?.image_created_with
                      }
                    >
                      <p class="text-xs text-muted italic mt-2 text-center">
                        Image generated with {professorResource()?.image_created_with}
                      </p>
                    </Show>
                  </div>
                  <Show when={auth.canModify(professorResource()?.created_by)}>
                    <MagicButton
                      variant="ghost"
                      size="sm"
                      class="w-full sm:w-auto"
                      onClick={() => void handleGenerateImage()}
                      isLoading={isGeneratingImage()}
                      loadingText="Generating..."
                    >
                      Generate Image
                    </MagicButton>
                  </Show>

                  {/* Voice Information Section - Hidden on mobile, shown on desktop */}
                  <div class="hidden md:block w-full mt-6">
                    <VoiceProfileSection
                      professorResource={professorResource}
                      voiceResource={voiceResource}
                    />
                  </div>
                </div>

                {/* Voice Information Section - Shown on mobile only, appears after details */}
                <div class="order-3 md:hidden w-full">
                  <VoiceProfileSection
                    professorResource={professorResource}
                    voiceResource={voiceResource}
                  />
                </div>
              </div>
              {/* End of two-column layout - No more full-width attributes div needed below */}

              {/* Courses Section */}
              <ProfessorCourses
                coursesResource={coursesResource}
                loading={coursesResource.loading}
                error={coursesResource.error as unknown}
              />
            </div>
          </Show>
        </Show>
      </Show>

      <ConfirmationModal
        isOpen={isDeleting()}
        title="Delete Professor"
        message={
          <div>
            <p>Are you sure you want to delete this professor?</p>
            <p class="mt-2 font-medium">This action cannot be undone.</p>
          </div>
        }
        confirmText="Delete Professor"
        onConfirm={() => void handleDelete()}
        onCancel={() => setIsDeleting(false)}
        isConfirming={isSubmitting()}
      />
    </div>
  )
}
