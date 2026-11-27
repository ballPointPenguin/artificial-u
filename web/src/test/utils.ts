import { render } from '@solidjs/testing-library'
import type { JSX } from '@solidjs/web'

// Custom render function to simplify testing
export function renderComponent(
  component: () => JSX.Element,
  options?: Parameters<typeof render>[1]
) {
  return render(component, options)
}

// Add any other test utilities here
