import type { Component, JSX, ParentProps } from 'solid-js'
import { splitProps } from 'solid-js'

interface FormActionsProps extends ParentProps {
  class?: string
  // Add any other specific layout-related props if needed, e.g., alignment
  // alignment?: 'left' | 'center' | 'right' | 'justify' (though 'justify-end' is common)
}

const FormActions: Component<FormActionsProps> = (props) => {
  const [local, others] = splitProps(props, ['class', 'children'])

  // Default classes from ProfessorForm example: flex justify-end space-x-3
  // We can make this configurable if needed via props later.
  const baseClasses = 'flex justify-end space-x-3 mt-6' // Added mt-6 for some top margin

  return (
    <div
      class={`${baseClasses} ${local.class || ''}`}
      {...others} // Pass through other native div attributes
    >
      {local.children}
    </div>
  )
}

export default FormActions