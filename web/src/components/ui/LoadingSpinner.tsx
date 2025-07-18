import { type Component } from 'solid-js'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'light' | 'dark'
  class?: string
}

export const LoadingSpinner: Component<LoadingSpinnerProps> = (props) => {
  const merged = {
    size: 'md' as const,
    variant: 'default' as const,
    ...props,
  }

  const getSizeClasses = () => {
    switch (merged.size) {
      case 'sm':
        return 'w-4 h-4'
      case 'lg':
        return 'w-6 h-6'
      default:
        return 'w-5 h-5'
    }
  }

  const getVariantClasses = () => {
    switch (merged.variant) {
      case 'light':
        return 'border-parchment-300 border-t-transparent'
      case 'dark':
        return 'border-parchment-600 border-t-transparent'
      default:
        return 'border-mystic-500 border-t-transparent'
    }
  }

  return (
    <div
      class={`inline-block border-2 rounded-full animate-spin ${getSizeClasses()} ${getVariantClasses()} ${merged.class || ''}`}
    />
  )
}