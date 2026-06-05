import type { Component } from 'solid-js'
import { Show } from 'solid-js'
import { useTranslations } from '../../i18n'
import { formatDateSimple } from '../../utils/formatDate'

interface MetadataInfoProps {
  type?: 'course' | 'lecture' | 'professor' | 'topic'
  createdBy?: {
    id: number
    name: string
    email?: string | null
  } | null
  createdWith?: string | null
  createdAt?: string | null
  class?: string
}

/**
 * MetadataInfo component displays creation metadata for assets
 * Shows asset type, creator, generator model, and date of creation
 */
const MetadataInfo: Component<MetadataInfoProps> = (props) => {
  const t = useTranslations()

  return (
    <Show when={props.createdBy || props.createdWith || props.createdAt}>
      <div class={`text-sm text-parchment-400 space-y-1 ${props.class || ''}`}>
        <Show when={props.type}>
          <p>
            <span class="font-medium">{t().metadata.type}:</span> {t().metadata.types[props.type!]}
          </p>
        </Show>
        <Show when={props.createdBy}>
          <p>
            <span class="font-medium">{t().metadata.createdBy}:</span> {props.createdBy?.name}
          </p>
        </Show>
        <Show when={props.createdWith}>
          <p>
            <span class="font-medium">{t().metadata.createdWith}:</span> {props.createdWith}
          </p>
        </Show>
        <Show when={props.createdAt}>
          <p>
            <span class="font-medium">{t().metadata.createdOn}:</span>{' '}
            {formatDateSimple(props.createdAt || '')}
          </p>
        </Show>
      </div>
    </Show>
  )
}

export default MetadataInfo
