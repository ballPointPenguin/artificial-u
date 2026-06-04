import type { Component } from 'solid-js'
import { useTranslations } from '../../i18n'

interface CourseStatusBadgeProps {
  status: string
  size?: 'sm' | 'md' | 'lg'
  class?: string
}

const sizeClasses: Record<NonNullable<CourseStatusBadgeProps['size']>, string> = {
  sm: 'gap-0.5 px-1.5 py-0.5 text-[9px]',
  md: 'gap-1 px-2 py-1 text-xs',
  lg: 'gap-1.5 px-3 py-1 text-sm',
}

const iconSizeClasses: Record<NonNullable<CourseStatusBadgeProps['size']>, string> = {
  sm: 'text-[8px]',
  md: 'text-[10px]',
  lg: 'text-xs',
}

const CourseStatusBadge: Component<CourseStatusBadgeProps> = (props) => {
  const t = useTranslations()
  const isPublished = () => props.status === 'published'
  const size = () => props.size ?? 'md'

  return (
    <span
      class={`inline-flex items-center font-medium rounded-full whitespace-nowrap border ${
        sizeClasses[size()]
      } ${
        isPublished()
          ? 'bg-success-bg text-success border-success-border'
          : 'bg-warning-bg text-warning border-warning-border'
      } ${props.class ?? ''}`}
    >
      <span class={iconSizeClasses[size()]}>{isPublished() ? '✓' : '●'}</span>
      <span class={size() === 'sm' ? 'uppercase tracking-tight' : ''}>
        {isPublished() ? t().courseDetail.published : t().courseDetail.hidden}
      </span>
    </span>
  )
}

export default CourseStatusBadge
