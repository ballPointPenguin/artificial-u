import type { JSX } from '@solidjs/web'
import type { Component } from 'solid-js'
import { omit } from 'solid-js'

interface NumberInputProps extends JSX.InputHTMLAttributes<HTMLInputElement> {
  error?: string | null | false
  class?: string
}

const NumberInput: Component<NumberInputProps> = (props) => {
  const others = omit(props, 'class', 'error')

  return (
    <input
      {...others}
      type="number"
      inputmode="numeric"
      class={`arcane-input ${props.class ?? ''} ${
        props.error ? 'border-red-500 focus-visible:outline-red-500' : ''
      }`}
    />
  )
}

export default NumberInput
