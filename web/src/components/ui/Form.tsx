import type { ComponentProps, JSX } from '@solidjs/web'
import type { Component, ParentProps } from 'solid-js'
import { omit } from 'solid-js'

interface FormProps extends ParentProps<Omit<ComponentProps<'form'>, 'children'>> {
  class?: string
  onSubmit?: JSX.EventHandler<HTMLFormElement, SubmitEvent>
  // Add any other specific form-related props if needed
}

const Form: Component<FormProps> = (props) => {
  const others = omit(props, 'class', 'children', 'onSubmit')

  const handleSubmit = (
    event: SubmitEvent & { currentTarget: HTMLFormElement; target: Element }
  ) => {
    if (props.onSubmit) {
      // Prevent default if onSubmit is provided, common practice for SPA forms
      event.preventDefault()
      props.onSubmit(event)
    }
    // If no onSubmit is provided, the native form submission will occur (or not, if prevented by a button type="button")
  }

  return (
    <form
      class={`space-y-6 ${props.class || ''}`} // Apply base spacing and any custom class
      onSubmit={handleSubmit}
      {...others} // Pass through other native form attributes
    >
      {props.children}
    </form>
  )
}

export default Form
