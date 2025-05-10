import { TextField as KTextField } from '@kobalte/core'
import type { Component, ComponentProps, JSX } from 'solid-js'
import { Show, splitProps } from 'solid-js'

// Define specific props for our Input component
interface InputProps extends Omit<ComponentProps<typeof KTextField.Input>, 'id'> {
  name: string // To be used by FormField for id generation
  label?: string // Optional: FormField will primarily handle the label
  error?: string | null | false // For error state styling
  value?: string | number | undefined
  // Keep onInput for standard SolidJS input handling if preferred by parent
  onInput?: JSX.EventHandler<HTMLInputElement, InputEvent>
  // Add onChange for compatibility with Kobalte's controlled pattern
  onChange?: (value: string) => void
  placeholder?: string
  type?: 'text' | 'number' | 'email' | 'password' | 'tel' | 'url' | 'search' | 'date'
  disabled?: boolean
  required?: boolean
  class?: string
  inputClass?: string // Specific class for the KTextField.Input
  // Allow any other KTextField.Input props to be passed through
  [key: string]: any
}

const Input: Component<InputProps> = (props) => {
  // Split props to separate our custom ones from those meant for KTextField.Input
  const [local, others] = splitProps(props, [
    'name', // Already used by FormField, KTextField.Root will also need it.
    'value',
    'onInput',
    'onChange', // Kobalte's controlled change
    'placeholder',
    'type',
    'disabled',
    'required',
    'class', // This class is for the root KTextField.Root
    'inputClass', // This class is for the KTextField.Input element
    'error', // Used for styling
    'label', // Primarily for FormField, but KTextField might need it for aria
  ])

  const fieldId = () => `field-${local.name}`
  const hasError = () => !!local.error

  const handleValueChange = (newValue: string) => {
    if (local.onChange) {
      local.onChange(newValue)
    }
    // If an onInput handler is also provided, we can call it.
    // This requires careful handling if both are used.
    // For now, prioritize local.onChange for Kobalte's controlled pattern.
    // If onInput is critical, the parent might need to adapt or this component needs a more complex event synthesis.
    if (local.onInput) {
        // Create a synthetic event if onInput expects it
        // This is a common pattern but can be tricky.
        // For simplicity, if onInput is primary, direct usage of KTextField.Input's onInput might be better.
        const syntheticEvent = {
            currentTarget: { value: newValue, name: local.name },
            target: { value: newValue, name: local.name },
            bubbles: true,
            cancelable: true,
        } as unknown as InputEvent & { currentTarget: HTMLInputElement; target: HTMLInputElement }
        // It's tricky to perfectly mimic native event objects.
        // Consider if `onChange` prop is sufficient for most use cases with Kobalte.
         local.onInput(syntheticEvent)
    }
  }

  return (
    <KTextField.Root
      name={local.name}
      value={local.value !== undefined ? String(local.value) : undefined}
      // Use KTextField.Root's onChange for controlled components
      onChange={handleValueChange}
      validationState={hasError() ? 'invalid' : 'valid'}
      disabled={local.disabled}
      required={local.required}
      class={local.class} // Class for the KTextField.Root
    >
      {/* For screen readers, if FormField isn't providing a visible label.
          Or if we decide Input can be used standalone.
          Kobalte's Label can be visually hidden. */}
      <Show when={local.label && KTextField.Label}>
        <KTextField.Label class="sr-only" as="label" for={fieldId()}>
          {local.label}
        </KTextField.Label>
      </Show>
      <KTextField.Input
        {...others} // Pass through remaining props
        id={fieldId()}
        type={local.type || 'text'}
        class={`arcane-input ${local.inputClass || ''}`} // Apply arcane-input and any custom inputClass
        aria-invalid={hasError()}
        aria-describedby={hasError() ? `${fieldId()}-error` : undefined}
      />
      {/* Kobalte also has KTextField.ErrorMessage and KTextField.Description
          but FormField is handling this for now. If Input can be standalone, we might add them here. */}
    </KTextField.Root>
  )
}

export default Input