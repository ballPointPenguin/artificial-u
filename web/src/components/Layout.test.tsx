import { screen } from '@solidjs/testing-library'
import { describe, expect, it } from 'vitest'
import { renderComponent } from '../test/utils'
import LayoutMock from './LayoutMock'

describe('Layout', () => {
  it('renders correctly', () => {
    renderComponent(() => <LayoutMock>Content</LayoutMock>)

    // Check if the navigation links are rendered
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()

    // Check if the content is rendered
    expect(screen.getByText('Content')).toBeInTheDocument()
  })
})
