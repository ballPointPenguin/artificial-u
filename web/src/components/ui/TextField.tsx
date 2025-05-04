import * as TextField from '@kobalte/core/text-field'
import { Show, createSignal, splitProps } from 'solid-js'

interface TextFieldProps extends TextField.TextFieldRootProps {
  label: string
  placeholder?: string
  helperText?: string
  error?: string
}

export function Input(props: TextFieldProps) {
  const [local, others] = splitProps(props, ['label', 'placeholder', 'helperText', 'error'])
  const [focused, setFocused] = createSignal(false)

  return (
    <TextField.Root {...others} validationState={local.error ? 'invalid' : 'valid'}>
      <TextField.Label class="block mb-2 text-sm font-serif text-parchment-200">
        {local.label}
      </TextField.Label>

      <TextField.Input
        placeholder={local.placeholder}
        class={`w-full px-4 py-2 bg-arcanum-800 border ${
          local.error
            ? 'border-red-500 focus:border-red-500'
            : focused()
              ? 'border-mystic-500'
              : 'border-parchment-700/30'
        } rounded-sm text-parchment-100 placeholder:text-parchment-500 focus:outline-none transition-colors duration-200`}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
      />

      <Show when={local.error}>
        <TextField.ErrorMessage class="mt-1 text-sm text-red-500">
          {local.error}
        </TextField.ErrorMessage>
      </Show>

      <Show when={!local.error && local.helperText}>
        <TextField.Description class="mt-1 text-sm text-parchment-400">
          {local.helperText}
        </TextField.Description>
      </Show>
    </TextField.Root>
  )
}
