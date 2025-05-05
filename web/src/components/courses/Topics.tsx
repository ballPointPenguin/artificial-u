import { For } from 'solid-js'
import { useCourseForm } from './FormContext'
import { WeekTopics } from './WeekTopics'
import type { TopicsProps } from './types'

export function Topics(props: TopicsProps) {
  const { form } = useCourseForm()

  return (
    <div>
      <h3 class="text-lg font-semibold mb-2 text-parchment-200">Course Topics</h3>
      <div class="space-y-4">
        <For each={Array.from({ length: form.total_weeks }, (_, w) => w + 1)}>
          {(week) => (
            <WeekTopics
              week={week}
              lecturesPerWeek={form.lectures_per_week}
              disabled={props.disabled}
            />
          )}
        </For>
      </div>
    </div>
  )
}
