import type { Component } from 'solid-js'
import { For, Show } from 'solid-js'
import type { Course } from '../../api/types.js'

interface ConnectedCoursesSelectProps {
  courses: Course[]
  value: number[]
  onChange: (value: number[]) => void
  disabled?: boolean
}

const ConnectedCoursesSelect: Component<ConnectedCoursesSelectProps> = (props) => {
  const toggleCourse = (courseId: number) => {
    if (props.value.includes(courseId)) {
      props.onChange(props.value.filter((id) => id !== courseId))
      return
    }

    props.onChange([...props.value, courseId])
  }

  return (
    <div class="max-h-56 space-y-2 overflow-y-auto rounded-lg border border-gray-300 bg-white p-3">
      <Show
        when={props.courses.length > 0}
        fallback={<p class="text-sm text-muted">No courses found in this department.</p>}
      >
        <For each={props.courses}>
          {(course) => (
            <label class="flex cursor-pointer items-center gap-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={props.value.includes(course.id)}
                onChange={() => toggleCourse(course.id)}
                disabled={props.disabled}
                class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span>{course.code ? `${course.code} — ${course.title}` : course.title}</span>
            </label>
          )}
        </For>
      </Show>
    </div>
  )
}

export default ConnectedCoursesSelect
