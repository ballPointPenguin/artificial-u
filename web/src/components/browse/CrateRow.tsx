import { type Component, For, Show } from 'solid-js'
import type { Course } from '../../api/types.js'
import { LoadingSpinner } from '../ui'
import CrateCard from './CrateCard.jsx'

interface CrateRowProps {
  title: string
  courses: Course[]
  loading?: boolean
}

/**
 * A horizontally snap-scrolling "crate" of course cards. The next card peeks
 * in from the edge, inviting a flip-through like a stack of records.
 */
const CrateRow: Component<CrateRowProps> = (props) => {
  return (
    <Show when={props.loading || props.courses.length > 0}>
      <section class="mb-8">
        <h2 class="section-label mb-3">{props.title}</h2>
        <Show when={!props.loading} fallback={<LoadingSpinner />}>
          <div class="-mx-4 flex snap-x snap-mandatory gap-4 overflow-x-auto scroll-px-4 px-4 pb-2">
            <For each={props.courses}>
              {(course) => (
                <CrateCard
                  course={course}
                  class="w-[72vw] max-w-[300px] shrink-0 snap-start md:w-[240px]"
                />
              )}
            </For>
          </div>
        </Show>
      </section>
    </Show>
  )
}

export default CrateRow
