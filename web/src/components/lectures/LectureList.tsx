import { For, Show, createEffect, createSignal } from 'solid-js'
import { lectureService } from '../../api/services/lecture-service.js'
import type { Lecture, APIError } from '../../api/types.js'
import { Button } from '../ui/Button.jsx'
import { Card, CardContent, CardFooter, CardHeader } from '../ui/Card.jsx' // Removed CardTitle
// import { Link } from '@solidjs/router' // Will be needed for navigation

interface LectureListProps {
  courseId: number
  version?: number // New optional prop to trigger refetch
  // onEditLecture: (lecture: Lecture) => void
  // onDeleteLecture: (lectureId: number) => void
  // onAddLecture: () => void
}

export function LectureList(props: LectureListProps) {
  const [lectures, setLectures] = createSignal<Lecture[]>([])
  const [isLoading, setIsLoading] = createSignal(false)
  const [error, setError] = createSignal<APIError | null>(null)

  createEffect(() => {
    // Depend on props.courseId and props.version
    // The effect will re-run if props.courseId or props.version changes.
    const currentCourseId = props.courseId
    // const currentVersion = props.version // Access version to make effect depend on it

    if (currentCourseId) {
      setIsLoading(true)
      setError(null)
      lectureService
        .listLectures({ courseId: currentCourseId, page: 1, size: 50 })
        .then((response) => {
          setLectures(response.items)
        })
        .catch((err: unknown) => {
          // Changed to unknown and will check type
          console.error('Failed to fetch lectures:', err)
          if (err instanceof Error) {
            setError({ detail: err.message })
          } else if (typeof err === 'object' && err !== null && 'detail' in err) {
            setError(err as APIError) // Assuming it might be an APIError object
          } else {
            setError({ detail: 'An unknown error occurred' })
          }
        })
        .finally(() => {
          setIsLoading(false)
        })
    }
  })

  const handleEdit = (lecture: Lecture) => {
    console.log('Edit lecture:', lecture)
    // props.onEditLecture(lecture)
  }

  const handleDelete = (lectureId: number) => {
    console.log('Delete lecture:', lectureId)
    // lectureService.deleteLecture(lectureId)
    //   .then(() => setLectures(prev => prev.filter(l => l.id !== lectureId)))
    //   .catch(err => console.error('Failed to delete lecture', err));
    // props.onDeleteLecture(lectureId)
  }

  const handleAddLecture = () => {
    console.log('Add new lecture for course:', props.courseId)
    // props.onAddLecture()
  }

  const getLectureDisplayTitle = (lecture: Lecture) => {
    if (lecture.summary)
      return lecture.summary.substring(0, 70) + (lecture.summary.length > 70 ? '...' : '')
    if (lecture.content)
      return lecture.content.substring(0, 70) + (lecture.content.length > 70 ? '...' : '')
    return `Lecture ID: ${String(lecture.id)}` // Explicitly cast to string
  }

  return (
    <div class="space-y-6 p-4">
      <div class="flex justify-between items-center">
        <h1 class="text-3xl font-display text-foreground">
          Lectures for Course <span class="font-bold">{props.courseId}</span>
        </h1>
        <Button
          onClick={() => {
            handleAddLecture()
          }}
          variant="outline"
        >
          Add New Lecture
        </Button>
      </div>

      <Show when={isLoading()}>
        <p class="text-muted-foreground text-center py-10">Loading lectures...</p>
      </Show>

      <Show when={error()}>
        <div
          class="p-4 mb-4 text-sm text-danger-foreground bg-danger-bg border border-danger-border rounded-lg"
          role="alert"
        >
          <span class="font-medium">Error fetching lectures:</span> {error()?.detail}
        </div>
      </Show>

      <Show when={!isLoading() && !error() && lectures().length === 0}>
        <p class="text-muted-foreground text-center py-10">No lectures found for this course.</p>
      </Show>

      <Show when={!isLoading() && lectures().length > 0}>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <For each={lectures()}>
            {(lecture) => (
              <Card bordered hover>
                <CardHeader>
                  <h3
                    class="text-lg font-semibold text-primary truncate"
                    title={getLectureDisplayTitle(lecture)}
                  >
                    {getLectureDisplayTitle(lecture)}
                  </h3>
                  <p class="text-xs text-muted-foreground">
                    ID: {lecture.id} | Topic ID: {lecture.topic_id} | Rev: {lecture.revision}
                  </p>
                </CardHeader>
                <CardContent>
                  <p class="text-sm text-muted-foreground line-clamp-3">
                    {lecture.content.substring(0, 150) +
                      (lecture.content.length > 150 ? '...' : '') ||
                      'No content preview available.'}
                  </p>
                </CardContent>
                <CardFooter class="flex justify-end space-x-2">
                  {/* <Link href={`/courses/${props.courseId}/lectures/${lecture.id}`}>
                    <Button variant="outline" size="sm">View</Button>
                  </Link> */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      handleEdit(lecture)
                    }}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    class="text-danger-foreground border-danger-border hover:bg-danger-bg/20 hover:text-danger-foreground"
                    onClick={() => {
                      handleDelete(lecture.id)
                    }}
                  >
                    Delete
                  </Button>
                </CardFooter>
              </Card>
            )}
          </For>
        </div>
      </Show>
    </div>
  )
}
