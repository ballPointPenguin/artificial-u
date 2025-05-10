import * as TextField from '@kobalte/core/text-field'
import { Show, splitProps } from 'solid-js'

interface TextFieldProps extends TextField.TextFieldRootProps {
  label: string
  placeholder?: string
  helperText?: string
  error?: string
}

export function Input(props: TextFieldProps) {
  const [local, others] = splitProps(props, ['label', 'placeholder', 'helperText', 'error'])

  const inputBaseClasses =
    'w-full px-4 py-2 rounded-sm bg-surface text-foreground placeholder:text-muted transition-colors duration-200 border focus:outline-none'

  const inputBorderClasses =
    'border-border focus:border-primary focus:ring-2 focus:ring-primary/50 ui-invalid:border-danger ui-invalid:focus:border-danger ui-invalid:focus:ring-danger/50'

  return (
    <TextField.Root {...others} validationState={local.error ? 'invalid' : 'valid'}>
      <TextField.Label class="block mb-2 text-sm font-serif text-muted">
        {local.label}
      </TextField.Label>

      <TextField.Input
        placeholder={local.placeholder}
        class={`${inputBaseClasses} ${inputBorderClasses}`}
      />

      <Show when={local.error}>
        <TextField.ErrorMessage class="mt-1 text-sm text-danger">
          {local.error}
        </TextField.ErrorMessage>
      </Show>

      <Show when={!local.error && local.helperText}>
        <TextField.Description class="mt-1 text-sm text-muted">
          {local.helperText}
        </TextField.Description>
      </Show>
    </TextField.Root>
  )
}
