import type { Component, ComponentProps, JSX, ParentProps } from 'solid-js'
import { splitProps } from 'solid-js'

interface FormProps extends ParentProps<Omit<ComponentProps<'form'>, 'children'>> {
  class?: string
  onSubmit?: JSX.EventHandler<HTMLFormElement, SubmitEvent>
  // Add any other specific form-related props if needed
}

const Form: Component<FormProps> = (props) => {
  const [local, others] = splitProps(props, ['class', 'children', 'onSubmit'])

  const handleSubmit = (event: SubmitEvent & { currentTarget: HTMLFormElement; target: Element }) => {
    if (local.onSubmit) {
      // Prevent default if onSubmit is provided, common practice for SPA forms
      event.preventDefault()
      local.onSubmit(event)
    }
    // If no onSubmit is provided, the native form submission will occur (or not, if prevented by a button type="button")
  }

  return (
    <form
      class={`space-y-6 ${local.class || ''}`} // Apply base spacing and any custom class
      onSubmit={props.onSubmit ? handleSubmit : undefined}
      {...others} // Pass through other native form attributes
    >
      {local.children}
    </form>
  )
}

export default Form