import { useParams } from '@solidjs/router' // Assuming usage of solid-router for params
import { Show, createSignal } from 'solid-js'
import { LectureList } from '../components/lectures/LectureList.jsx'
import { LectureForm } from '../components/lectures/LectureForm.jsx'
import type { Lecture, LectureCreate, LectureUpdate, APIError } from '../api/types.js'
import { lectureService } from '../api/services/lecture-service.js'
import { Button } from '../components/ui/Button.jsx'

// This page would typically get courseId from route params
export default function CourseLecturesPage() {
  const params = useParams() // Example: /courses/:courseId/lectures
  const courseId = () => parseInt(params.courseId || '0', 10)

  const [showForm, setShowForm] = createSignal(false)
  const [editingLecture, setEditingLecture] = createSignal<Lecture | null>(null)
  const [isLoading, setIsLoading] = createSignal(false)
  const [formError, setFormError] = createSignal<APIError | null>(null)

  // Signal to trigger refetching the list, e.g., after create/update/delete
  const [listVersion, setListVersion] = createSignal(0)

  const handleAddLecture = () => {
    setEditingLecture(null)
    setShowForm(true)
    setFormError(null)
  }

  const handleCancelForm = () => {
    setShowForm(false)
    setEditingLecture(null)
    setFormError(null)
  }

  const handleSubmitForm = async (data: LectureCreate | LectureUpdate) => {
    setIsLoading(true)
    setFormError(null)
    try {
      const currentEditingLecture = editingLecture()
      if (currentEditingLecture) {
        await lectureService.updateLecture(currentEditingLecture.id, data as LectureUpdate)
      } else {
        await lectureService.createLecture(data as LectureCreate)
      }
      setShowForm(false)
      setEditingLecture(null)
      setListVersion((v) => v + 1) // Trigger list refetch
    } catch (err: unknown) {
      console.error('Failed to save lecture:', err)
      if (err instanceof Error) {
        setFormError({ detail: err.message })
      } else if (typeof err === 'object' && err !== null && 'detail' in err) {
        setFormError(err as APIError)
      } else {
        setFormError({ detail: 'An unknown error occurred while saving the lecture.' })
      }
    } finally {
      setIsLoading(false)
    }
  }

  // This is a mock for how LectureList would trigger edit/add.
  // In a real scenario, LectureList would emit events or use context/stores.
  // For now, CourseLecturesPage will control form visibility and pass callbacks (conceptually).
  // The actual LectureList created earlier doesn't have these specific callbacks wired up yet.
  // We can refine LectureList to accept onAdd/onEdit callbacks later.

  return (
    <div class="container mx-auto p-4 space-y-8">
      <Show
        when={!showForm()}
        fallback={
          <LectureForm
            courseId={courseId()}
            existingLecture={editingLecture()}
            onSubmit={handleSubmitForm}
            onCancel={handleCancelForm}
            isLoading={isLoading()}
            error={formError()}
          />
        }
      >
        <div class="flex justify-between items-center mb-6">
          {/* Title is inside LectureList, we could lift it here if needed */}
          {/* This button might be redundant if LectureList has its own "Add" button that calls handleAddLecture */}
          <Button onClick={handleAddLecture} variant="primary">
            Create New Lecture
          </Button>
        </div>
        {/* Pass listVersion as a key to LectureList to force re-render and refetch when it changes */}
        <LectureList courseId={courseId()} version={listVersion()} />

        {/* To integrate edit/delete from list items, LectureList would need to call
            handleEditLecture or a handleDeleteLecture function defined here.
            Example placeholder for triggering edit from outside the list:
            <Button onClick={() => editingLecture() && handleEditLecture(editingLecture()!)}>Edit Selected (Test)</Button>
        */}
      </Show>
    </div>
  )
}
