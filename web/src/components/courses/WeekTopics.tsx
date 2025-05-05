import { For } from 'solid-js'
import { TopicInput } from './TopicInput'
import type { WeekTopicsProps } from './types'

export function WeekTopics(props: WeekTopicsProps) {
  return (
    <div class="border border-parchment-800 rounded p-3 bg-parchment-950/30">
      <div class="font-semibold text-parchment-300 mb-2">Week {props.week}</div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
        <For each={Array.from({ length: props.lecturesPerWeek }, (_, l) => l + 1)}>
          {(order) => <TopicInput week={props.week} order={order} disabled={props.disabled} />}
        </For>
      </div>
    </div>
  )
}
