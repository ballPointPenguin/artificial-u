import { A, useNavigate, useParams } from '@solidjs/router'
import { type Component, createResource, createSignal, For, Show } from 'solid-js'
import { departmentService } from '../../api/services/department-service.js'
import { professorService } from '../../api/services/professor-service.js'
import { getVoice, manualAssignVoice } from '../../api/services/voice-service.js'
import type {
  LectureBrief,
  Professor,
  ProfessorCourseBrief,
  ProfessorCoursesResponse,
} from '../../api/types.js'
import { RequireAuth } from '../../auth/RequireAuth'
import { Alert, Button, ConfirmationModal, LoadingSpinner, MagicButton } from '../ui'
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
                      <span>Level: {course.level}</span> | <span>Credits: {course.credits}</span>
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

export default function ProfessorDetail() {
  const params = useParams()
  const navigate = useNavigate()
  const [isEditing, setIsEditing] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')
  const [isGeneratingImage, setIsGeneratingImage] = createSignal(false)
  const [generationError, setGenerationError] = createSignal('')
  const [isImageLoading, setIsImageLoading] = createSignal(false)
  const [isAssigningVoice, setIsAssigningVoice] = createSignal(false)
  const [voiceAssignError, setVoiceAssignError] = createSignal('')
  // Manual voice entry state
  const [manualElVoiceId, setManualElVoiceId] = createSignal('')
  const [isAssigningManual, setIsAssigningManual] = createSignal(false)

  const [professorResource, { refetch: refetchProfessor }] = createResource(
    () => {
      const id = Number.parseInt(params.id, 10)
      if (Number.isNaN(id)) {
        throw new Error('Professor ID is missing or invalid')
      }
      return id
    },
    async (id) => {
      setIsImageLoading(false) // Reset image loading state when professor data changes
      setVoiceAssignError('') // Clear voice assignment error when professor data changes
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

  // Fetch professor's lectures to detect if any existing audio has been generated
  const [lecturesResource] = createResource(
    () => professorResource()?.id,
    async (professorId: number) => {
      if (professorId) {
        return professorService.getProfessorLectures(professorId)
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
      const id = Number.parseInt(params.id, 10)
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
      const id = Number.parseInt(params.id, 10)
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
      const id = Number.parseInt(params.id, 10)
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

  const handleAssignVoice = async () => {
    setIsAssigningVoice(true)
    setVoiceAssignError('')
    setError('')

    try {
      const id = Number.parseInt(params.id, 10)
      if (Number.isNaN(id)) {
        throw new Error('Invalid professor ID')
      }

      // Phase 2: warn if reassigning and lectures already have audio
      const hasExistingVoice = Boolean(professorResource()?.voice_id)
      const lecturesResponse = lecturesResource()
      const lectures: LectureBrief[] | undefined = lecturesResponse?.lectures
      const hasAudio = Array.isArray(lectures) && lectures.some((l) => l.audio_url != null)
      if (hasExistingVoice && hasAudio) {
        const proceed = window.confirm(
          'This professor already has lectures with generated audio. Reassigning the voice may make future audio sound different. Are you sure you want to continue?'
        )
        if (!proceed) {
          return
        }
      }

      await professorService.assignVoiceToProfessor(id)
      void refetchProfessor()
    } catch (error) {
      setVoiceAssignError(error instanceof Error ? error.message : 'Failed to assign voice')
    } finally {
      setIsAssigningVoice(false)
    }
  }

  const handleManualAssign = async () => {
    setIsAssigningManual(true)
    setVoiceAssignError('')
    try {
      const professorId = Number.parseInt(params.id, 10)
      if (Number.isNaN(professorId)) throw new Error('Invalid professor ID')

      // Warn if reassigning and there is audio
      const hasExistingVoice = Boolean(professorResource()?.voice_id)
      const lecturesResponse = lecturesResource()
      const lectures: LectureBrief[] | undefined = lecturesResponse?.lectures
      const hasAudio = Array.isArray(lectures) && lectures.some((l) => l.audio_url != null)
      if (hasExistingVoice && hasAudio) {
        const proceed = window.confirm(
          'This professor already has lectures with generated audio. Reassigning the voice may make future audio sound different. Are you sure you want to continue?'
        )
        if (!proceed) return
      }

      const elId = manualElVoiceId().trim()
      if (!elId) throw new Error('Please enter a voice_id to assign')
      await manualAssignVoice(String(professorId), { el_voice_id: elId })
      setManualElVoiceId('')
      void refetchProfessor()
    } catch (error) {
      setVoiceAssignError(error instanceof Error ? error.message : 'Failed to assign voice')
    } finally {
      setIsAssigningManual(false)
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
                <RequireAuth>
                  <h2 class="text-xl font-semibold mb-4">Edit Professor</h2>
                  <ProfessorForm
                    professor={professorResource() as Professor}
                    onSubmit={handleSubmitUpdate}
                    onCancel={() => setIsEditing(false)}
                    isSubmitting={isSubmitting()}
                    error={error()}
                  />
                </RequireAuth>
              </div>
            }
          >
            <div>
              <div class="flex justify-between items-center mb-6">
                <h1 class="text-3xl font-display text-parchment-100 text-shadow-golden">
                  {professorResource()?.name}
                </h1>
                <div class="flex space-x-2 items-center">
                  <RequireAuth>
                    <Show when={!isGeneratingImage()}>
                      <MagicButton
                        variant="ghost"
                        size="sm"
                        onClick={() => void handleGenerateImage()}
                        isLoading={isGeneratingImage()}
                        loadingText="Generating..."
                      >
                        Generate Image
                      </MagicButton>
                    </Show>
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
                  </RequireAuth>
                </div>
              </div>

              <Show when={generationError()}>
                <Alert variant="danger" class="mb-4">
                  <p>Error generating image: {generationError()}</p>
                </Alert>
              </Show>

              {/* Start of two-column layout for md screens and up */}
              <div class="md:flex md:gap-8 mb-6">
                {/* Left Column: All Attributes */}
                <div class="md:w-1/2 space-y-3 text-muted">
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

                {/* Right Column: Image */}
                <div class="md:w-1/2 mt-6 md:mt-0">
                  <div class="relative flex items-center justify-center min-h-[200px] bg-surface rounded-lg">
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
                  </div>

                  {/* Voice Information Section */}
                  <div class="mt-6">
                    <h3 class="text-lg font-display text-parchment-100 mb-3 text-shadow-golden">
                      Voice Profile
                    </h3>
                    <div class="bg-surface rounded-lg p-4 space-y-2">
                      <Show when={professorResource()?.voice_id}>
                        <p class="text-sm text-muted">
                          <strong class="font-semibold text-foreground">Voice ID:</strong>{' '}
                          {professorResource()?.voice_id}
                        </p>

                        <Show when={!voiceResource.loading && voiceResource()}>
                          {(voice) => (
                            <>
                              <Show when={voice().name}>
                                <p class="text-sm text-muted">
                                  <strong class="font-semibold text-foreground">Name:</strong>{' '}
                                  {voice().name}
                                </p>
                              </Show>

                              <Show when={voice().accent}>
                                <p class="text-sm text-muted">
                                  <strong class="font-semibold text-foreground">Accent:</strong>{' '}
                                  {voice().accent}
                                </p>
                              </Show>

                              <Show when={voice().gender}>
                                <p class="text-sm text-muted">
                                  <strong class="font-semibold text-foreground">Gender:</strong>{' '}
                                  {voice().gender}
                                </p>
                              </Show>

                              <Show when={voice().age}>
                                <p class="text-sm text-muted">
                                  <strong class="font-semibold text-foreground">Age:</strong>{' '}
                                  {voice().age}
                                </p>
                              </Show>

                              <Show when={voice().language}>
                                <p class="text-sm text-muted">
                                  <strong class="font-semibold text-foreground">Language:</strong>{' '}
                                  {voice().language}
                                </p>
                              </Show>

                              <Show when={voice().description}>
                                <p class="text-sm text-muted">
                                  <strong class="font-semibold text-foreground">
                                    Description:
                                  </strong>
                                  <span class="block mt-1 whitespace-pre-wrap">
                                    {voice().description}
                                  </span>
                                </p>
                              </Show>

                              <Show when={voice().preview_url}>
                                <div class="mt-3">
                                  <audio
                                    controls
                                    class="w-full max-w-sm"
                                    aria-label="Voice preview"
                                  >
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

                        <Show when={voiceResource.loading}>
                          <p class="text-sm text-muted italic">Loading voice details...</p>
                        </Show>

                        <Show when={voiceResource.error as unknown}>
                          <p class="text-sm text-danger">
                            Error loading voice details: {getErrorMessage(voiceResource.error)}
                          </p>
                        </Show>
                      </Show>

                      {/* Assign/reassign & Voice ID Override inline controls */}
                      <div class="mt-3">
                        <Show when={voiceAssignError()}>
                          <Alert variant="danger" class="text-sm mb-2">
                            {voiceAssignError()}
                          </Alert>
                        </Show>
                        <RequireAuth>
                          <div class="flex flex-col sm:flex-row sm:items-center sm:space-x-3 space-y-2 sm:space-y-0">
                            <MagicButton
                              variant="secondary"
                              size="sm"
                              onClick={() => void handleAssignVoice()}
                              disabled={isAssigningVoice()}
                              isLoading={isAssigningVoice()}
                              loadingText="Assigning..."
                            >
                              {professorResource()?.voice_id ? 'Reassign Voice' : 'Assign Voice'}
                            </MagicButton>
                            <div class="flex items-center space-x-2">
                              <input
                                type="text"
                                class="input input-bordered w-full sm:w-64"
                                placeholder="Voice ID Override"
                                value={manualElVoiceId()}
                                onInput={(e) =>
                                  setManualElVoiceId((e.target as HTMLInputElement).value)
                                }
                                aria-label="Voice ID Override"
                              />
                              <MagicButton
                                size="sm"
                                variant="primary"
                                onClick={() => void handleManualAssign()}
                                disabled={!manualElVoiceId().trim() || isAssigningManual()}
                                isLoading={isAssigningManual()}
                                loadingText="Overriding..."
                              >
                                Override
                              </MagicButton>
                            </div>
                          </div>
                        </RequireAuth>
                      </div>
                    </div>
                  </div>
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
