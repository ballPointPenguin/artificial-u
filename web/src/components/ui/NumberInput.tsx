import type { Component, JSX } from 'solid-js'
import { splitProps } from 'solid-js'

interface NumberInputProps extends JSX.InputHTMLAttributes<HTMLInputElement> {
  error?: string | null | false
  class?: string
}

const NumberInput: Component<NumberInputProps> = (props) => {
  const [local, others] = splitProps(props, ['class', 'error'])

  return (
    <input
      type="number"
      inputMode="numeric"
      class={`arcane-input ${local.class ?? ''} ${local.error ? 'border-red-500 focus-visible:outline-red-500' : ''}`}
      {...others}
    />
  )
}

export default NumberInput
