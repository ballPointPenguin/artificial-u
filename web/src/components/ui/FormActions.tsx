import type { Component, ParentProps } from 'solid-js'
import { omit } from 'solid-js'

interface FormActionsProps extends ParentProps {
  class?: string
  // Add any other specific layout-related props if needed, e.g., alignment
  // alignment?: 'left' | 'center' | 'right' | 'justify' (though 'justify-end' is common)
}

const FormActions: Component<FormActionsProps> = (props) => {
  const others = omit(props, 'class', 'children')

  // Default classes from ProfessorForm example: flex justify-end space-x-3
  // We can make this configurable if needed via props later.
  const baseClasses = 'flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-end mt-6' // Added mt-6 for top margin

  return (
    <div
      class={`${baseClasses} ${props.class || ''}`}
      {...others} // Pass through other native div attributes
    >
      {props.children}
    </div>
  )
}

export default FormActions
