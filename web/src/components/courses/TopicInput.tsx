import type { CourseTopic } from '../../api/types'
import { useCourseForm } from './FormContext'
import type { TopicInputProps } from './types'

export function TopicInput(props: TopicInputProps) {
  const { form, updateTopicTitle } = useCourseForm()

  const topic = form.topics.find(
    (t: CourseTopic) => t.week_number === props.week && t.order_in_week === props.order
  ) || { week_number: props.week, order_in_week: props.order, title: '' }

  const handleInput = (e: InputEvent & { currentTarget: HTMLInputElement }) => {
    updateTopicTitle(props.week, props.order, e.currentTarget.value)
  }

  return (
    <div>
      <label class="block text-xs text-parchment-400 mb-1">Lecture {String(props.order)}</label>
      <input
        type="text"
        value={topic.title}
        onInput={handleInput}
        class="arcane-input text-sm"
        placeholder={`Lecture ${String(props.order)} title`}
        disabled={props.disabled}
      />
    </div>
  )
}
