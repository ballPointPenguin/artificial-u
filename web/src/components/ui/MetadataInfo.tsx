import type { Component } from 'solid-js'
import { Show } from 'solid-js'
import { formatDateSimple } from '../../utils/formatDate'

interface MetadataInfoProps {
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
 * Shows "Created By {student name}", "Created with {model name}", "Created on {date}"
 */
const MetadataInfo: Component<MetadataInfoProps> = (props) => {
  return (
    <Show when={props.createdBy || props.createdWith || props.createdAt}>
      <div class={`text-sm text-parchment-400 space-y-1 ${props.class || ''}`}>
        <Show when={props.createdBy}>
          <p>
            <span class="font-medium">Created By:</span> {props.createdBy?.name}
          </p>
        </Show>
        <Show when={props.createdWith}>
          <p>
            <span class="font-medium">Created with:</span> {props.createdWith}
          </p>
        </Show>
        <Show when={props.createdAt}>
          <p>
            <span class="font-medium">Created on:</span> {formatDateSimple(props.createdAt || '')}
          </p>
        </Show>
      </div>
    </Show>
  )
}

export default MetadataInfo
