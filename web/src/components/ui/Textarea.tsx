import { TextField as KTextField } from '@kobalte/core'
import type { Component, ComponentProps, JSX } from 'solid-js'
import { Show, splitProps } from 'solid-js'

interface TextareaProps extends Omit<ComponentProps<typeof KTextField.TextArea>, 'id'> {
  name: string
  label?: string // Optional: FormField will primarily handle the label
  error?: string | null | false
  value?: string | undefined
  onInput?: JSX.EventHandler<HTMLTextAreaElement, InputEvent>
  onChange?: (value: string) => void // For Kobalte's controlled pattern
  placeholder?: string
  rows?: number
  disabled?: boolean
  required?: boolean
  class?: string // For KTextField.Root
  textareaClass?: string // Specific class for KTextField.TextArea
  [key: string]: any
}

const Textarea: Component<TextareaProps> = (props) => {
  const [local, others] = splitProps(props, [
    'name',
    'value',
    'onInput',
    'onChange',
    'placeholder',
    'rows',
    'disabled',
    'required',
    'class',
    'textareaClass',
    'error',
    'label',
  ])

  const fieldId = () => `field-${local.name}`
  const hasError = () => !!local.error

  const handleValueChange = (newValue: string) => {
    if (local.onChange) {
      local.onChange(newValue)
    }
    if (local.onInput) {
      // Similar to Input, create a synthetic event if onInput expects it.
      const syntheticEvent = {
        currentTarget: { value: newValue, name: local.name },
        target: { value: newValue, name: local.name },
        bubbles: true,
        cancelable: true,
      } as unknown as InputEvent & { currentTarget: HTMLTextAreaElement; target: HTMLTextAreaElement }
      local.onInput(syntheticEvent)
    }
  }

  return (
    <KTextField.Root
      name={local.name}
      value={local.value}
      onChange={handleValueChange}
      validationState={hasError() ? 'invalid' : 'valid'}
      disabled={local.disabled}
      required={local.required}
      class={local.class} // Class for KTextField.Root
    >
      <Show when={local.label && KTextField.Label}>
        <KTextField.Label class="sr-only" as="label" for={fieldId()}>
          {local.label}
        </KTextField.Label>
      </Show>
      <KTextField.TextArea
        {...others}
        id={fieldId()}
        class={`arcane-input ${local.textareaClass || ''}`} // Apply arcane-input
        rows={local.rows || 3} // Default rows
        aria-invalid={hasError()}
        aria-describedby={hasError() ? `${fieldId()}-error` : undefined}
      />
    </KTextField.Root>
  )
}

export default Textarea