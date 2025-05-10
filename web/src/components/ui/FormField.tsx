import type { Component, JSX, ParentProps } from 'solid-js'
import { Show } from 'solid-js'

interface FormFieldProps extends ParentProps {
  label: string
  name: string // for `htmlFor` and potentially other uses
  error?: string | null | false
  required?: boolean
  helperText?: string | JSX.Element
  labelClass?: string
  inputClass?: string // Class for the wrapper around the children (input element)
  errorClass?: string
  helperTextClass?: string
}

const FormField: Component<FormFieldProps> = (props) => {
  const fieldId = () => `field-${props.name}`

  return (
    <div class="mb-4">
      <Show when={props.label}>
        <label
          for={fieldId()}
          class={`block text-sm font-medium mb-1 text-foreground ${props.labelClass || ''}`}
        >
          {props.label}
          <Show when={props.required}>
            <span class="text-danger ml-1">*</span>
          </Show>
        </label>
      </Show>
      <div class={`mt-1 ${props.inputClass || ''}`}>
        {/* We'll pass the actual input component as children,
            and might need to clone it to pass down id, describedBy etc. */}
        {props.children}
      </div>
      <Show when={props.helperText && !props.error}>
        <p
          class={`mt-1 text-xs text-muted ${props.helperTextClass || ''}`}
          id={`${fieldId()}-helper`}
        >
          {props.helperText}
        </p>
      </Show>
      <Show when={props.error}>
        <p class={`mt-1 text-sm text-danger ${props.errorClass || ''}`} id={`${fieldId()}-error`}>
          {props.error}
        </p>
      </Show>
    </div>
  )
}

export default FormField
