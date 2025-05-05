import { Show } from 'solid-js'
import { useCourseForm } from './FormContext'
import type { DescriptionProps } from './types'

export function Description(props: DescriptionProps) {
  const { form, errors, updateForm } = useCourseForm()

  const handleChange = (e: InputEvent & { currentTarget: HTMLTextAreaElement }) => {
    const { name, value } = e.currentTarget
    updateForm(name, value)
  }

  return (
    <div>
      <label for="description" class="block text-sm font-medium mb-1 text-parchment-300">
        Description*
      </label>
      <textarea
        id="description"
        name="description"
        rows={4}
        value={form.description}
        onInput={handleChange}
        class="arcane-input w-full"
        classList={{
          'border-red-500': !!errors.description,
        }}
        placeholder="Course description"
        disabled={props.disabled}
      />
      <Show when={errors.description}>
        <p class="mt-1 text-sm text-red-600">{errors.description}</p>
      </Show>
    </div>
  )
}
