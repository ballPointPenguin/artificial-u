import { TextField as KTextField } from '@kobalte/core/text-field'
import type { ComponentProps, JSX } from '@solidjs/web'
import type { Component } from 'solid-js'
import { omit, Show } from 'solid-js'

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
}

const Textarea: Component<TextareaProps> = (props) => {
  const others = omit(
    props,
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
    'label'
  )

  const fieldId = () => `field-${props.name}`
  const hasError = () => !!props.error

  const handleValueChange = (newValue: string) => {
    if (props.onChange) {
      props.onChange(newValue)
    }
    if (props.onInput) {
      // Similar to Input, create a synthetic event if onInput expects it.
      const syntheticEvent = {
        currentTarget: { value: newValue, name: props.name },
        target: { value: newValue, name: props.name },
        bubbles: true,
        cancelable: true,
      } as unknown as InputEvent & {
        currentTarget: HTMLTextAreaElement
        target: HTMLTextAreaElement
      }
      props.onInput(syntheticEvent)
    }
  }

  return (
    <KTextField
      name={props.name}
      value={props.value}
      onChange={handleValueChange}
      validationState={hasError() ? 'invalid' : 'valid'}
      disabled={props.disabled}
      required={props.required}
      class={props.class} // Class for KTextField root
    >
      <Show when={props.label && KTextField.Label}>
        <KTextField.Label class="sr-only" as="label" for={fieldId()}>
          {props.label}
        </KTextField.Label>
      </Show>
      <KTextField.TextArea
        {...others}
        id={fieldId()}
        class={`arcane-input ${props.textareaClass || ''}`} // Apply arcane-input
        rows={props.rows || 3} // Default rows
        aria-invalid={hasError() ? 'true' : 'false'}
        aria-describedby={hasError() ? `${fieldId()}-error` : undefined}
      />
    </KTextField>
  )
}

export default Textarea
