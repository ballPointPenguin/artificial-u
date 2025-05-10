import { useNavigate, useParams } from '@solidjs/router'
import { Show, createResource, createSignal } from 'solid-js'
import { professorService } from '../../api/services/professor-service.js'
import type { Professor } from '../../api/types.js'
import { Alert, Button, ConfirmationModal } from '../ui'
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

  // Fetch the specific professor using createResource
  const [professorResource, { refetch }] = createResource(() => {
    const id = Number.parseInt(params.id, 10)
    if (Number.isNaN(id)) {
      throw new Error('Professor ID is missing or invalid')
    }
    return id
  }, professorService.getProfessor)

  // Type-safe helper to get error message
  const getErrorMessage = () => {
    const error: unknown = professorResource.error
    return error instanceof Error ? error.message : 'Unknown error'
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
      void refetch()
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
      // Navigate back to professors list after deletion
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
      void refetch()
    } catch (error) {
      setGenerationError(error instanceof Error ? error.message : 'Failed to generate image')
    } finally {
      setIsGeneratingImage(false)
    }
  }

  return (
    <div class="arcane-card p-8">
      {/* Loading and error states */}
      <Show
        when={!professorResource.loading}
        fallback={<p class="text-muted">Loading professor details...</p>}
      >
        <Show
          when={!professorResource.error}
          fallback={
            <Alert variant="danger" class="mb-4">
              <p>Error loading professor: {getErrorMessage()}</p>
              <Button variant="ghost" size="sm" onClick={() => void refetch()} class="mt-2">
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
            {/* Professor details display */}
            <div>
              <div class="flex justify-between items-center mb-6">
                <h1 class="text-3xl font-display text-parchment-100 text-shadow-golden">
                  {professorResource()?.name}
                </h1>
                <div class="flex space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => void handleGenerateImage()}
                    disabled={isGeneratingImage()}
                  >
                    {isGeneratingImage() ? 'Generating...' : 'Generate Image'}
                  </Button>
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

              {/* Display generation error if any */}
              <Show when={generationError()}>
                <Alert variant="danger" class="mb-4">
                  <p>Error generating image: {generationError()}</p>
                </Alert>
              </Show>

              <div class="space-y-3 text-muted">
                <p>
                  <strong class="font-semibold text-foreground">Title:</strong>{' '}
                  <span class="text-muted">{professorResource()?.title}</span>
                </p>
                <p>
                  <strong class="font-semibold text-foreground">Specialization:</strong>{' '}
                  <span class="text-muted">{professorResource()?.specialization}</span>
                </p>

                <Show when={professorResource()?.description}>
                  <p>
                    <strong class="font-semibold text-foreground">Description:</strong>
                    <span class="block mt-1 whitespace-pre-wrap text-muted">
                      {professorResource()?.description}
                    </span>
                  </p>
                </Show>

                <Show when={professorResource()?.background}>
                  <p>
                    <strong class="font-semibold text-foreground">Background:</strong>
                    <span class="block mt-1 whitespace-pre-wrap text-muted">
                      {professorResource()?.background}
                    </span>
                  </p>
                </Show>

                <Show when={professorResource()?.teaching_style}>
                  <p>
                    <strong class="font-semibold text-foreground">Teaching Style:</strong>{' '}
                    <span class="text-muted">{professorResource()?.teaching_style}</span>
                  </p>
                </Show>

                <Show when={professorResource()?.personality}>
                  <p>
                    <strong class="font-semibold text-foreground">Personality:</strong>{' '}
                    <span class="text-muted">{professorResource()?.personality}</span>
                  </p>
                </Show>

                {/* Display image if available */}
                <Show when={professorResource()?.image_url}>
                  <p class="font-semibold text-foreground mt-4">Profile Image:</p>
                  <img
                    src={
                      professorResource()?.image_url ? String(professorResource()?.image_url) : ''
                    }
                    alt={`Professor ${String(professorResource()?.name || '')}`}
                    class="mt-2 max-w-xs h-auto rounded-lg shadow-lg"
                    onError={(e) => {
                      console.error('Image failed to load:', e.currentTarget.src)
                    }}
                  />
                </Show>
              </div>
            </div>
          </Show>
        </Show>
      </Show>

      {/* Delete confirmation modal */}
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
