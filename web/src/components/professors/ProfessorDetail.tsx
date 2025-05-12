import { A, useNavigate, useParams } from '@solidjs/router'
import { For, Show, createResource, createSignal } from 'solid-js'
import { professorService } from '../../api/services/professor-service.js'
import { departmentService } from '../../api/services/department-service.js'
import type { Professor, ProfessorCourseBrief } from '../../api/types.js'
import { Alert, Button, ConfirmationModal, MagicButton } from '../ui'
import ProfessorForm, { type ProfessorFormData } from './ProfessorForm.js'

export default function ProfessorDetail() {
  const params = useParams()
  const navigate = useNavigate()
  const [isEditing, setIsEditing] = createSignal(false)
  const [isDeleting, setIsDeleting] = createSignal(false)
  const [isSubmitting, setIsSubmitting] = createSignal(false)
  const [error, setError] = createSignal('')
  const [isGeneratingImage, setIsGeneratingImage] = createSignal(false)
  const [generationError, setGenerationError] = createSignal('')

  const [professorResource, { refetch: refetchProfessor }] = createResource(() => {
    const id = Number.parseInt(params.id, 10)
    if (Number.isNaN(id)) {
      throw new Error('Professor ID is missing or invalid')
    }
    return id
  }, professorService.getProfessor)

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
                <h2 class="text-xl font-semibold mb-4">Edit Professor</h2>
                <ProfessorForm
                  professor={professorResource() as Professor}
                  onSubmit={handleSubmitUpdate}
                  onCancel={() => setIsEditing(false)}
                  isSubmitting={isSubmitting()}
                  error={error()}
                />
              </div>
            }
          >
            <div>
              <div class="flex justify-between items-center mb-6">
                <h1 class="text-3xl font-display text-parchment-100 text-shadow-golden">
                  {professorResource()?.name}
                </h1>
                <div class="flex space-x-2 items-center">
                  <Show when={!professorResource()?.image_url && !isGeneratingImage()}>
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
                        <span class="text-muted">{style()}</span>
                      </p>
                    )}
                  </Show>

                  <Show when={professorResource()?.personality}>
                    {(pers) => (
                      <p>
                        <strong class="font-semibold text-foreground">Personality:</strong>{' '}
                        <span class="text-muted">{pers()}</span>
                      </p>
                    )}
                  </Show>
                </div>

                {/* Right Column: Image */}
                <div class="md:w-1/2 mt-6 md:mt-0">
                  <Show when={professorResource()?.image_url}>
                    <img
                      src={professorResource()?.image_url ?? ''}
                      alt={`Professor ${professorResource()?.name || ''}`}
                      class="w-full max-w-sm h-auto rounded-lg shadow-lg object-contain"
                      onError={(e) => {
                        // biome-ignore lint/suspicious/noConsoleLog: Intended for debugging
                        console.log('Image failed to load:', (e.target as HTMLImageElement).src)
                      }}
                    />
                  </Show>
                </div>
              </div>
              {/* End of two-column layout - No more full-width attributes div needed below */}

              {/* Courses Section */}
              <div class="mt-8">
                <h2 class="text-2xl font-display text-parchment-100 mb-4 text-shadow-golden">
                  Courses Taught
                </h2>
                <Show
                  when={!coursesResource.loading}
                  fallback={<p class="text-muted">Loading courses...</p>}
                >
                  <Show
                    when={!coursesResource.error}
                    fallback={
                      <Alert variant="danger">
                        Error loading courses:{' '}
                        {coursesResource.error instanceof Error
                          ? coursesResource.error.message
                          : 'Unknown error'}
                      </Alert>
                    }
                  >
                    <Show
                      /* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */
                      when={coursesResource()?.courses && coursesResource()!.courses.length > 0}
                      fallback={
                        <p class="text-muted">
                          This professor is not currently teaching any courses.
                        </p>
                      }
                    >
                      <ul class="space-y-2">
                        <For each={coursesResource()?.courses}>
                          {(course: ProfessorCourseBrief) => (
                            <li class="arcane-card-sm p-3">
                              <A href={`/courses/${String(course.id)}`} class="hover:text-primary">
                                <strong class="font-semibold text-foreground">
                                  {course.code}:
                                </strong>{' '}
                                {course.title}
                              </A>
                              <div class="text-xs text-muted mt-1">
                                <span>Level: {course.level}</span> |{' '}
                                <span>Credits: {course.credits}</span>
                              </div>
                            </li>
                          )}
                        </For>
                      </ul>
                    </Show>
                  </Show>
                </Show>
              </div>
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
