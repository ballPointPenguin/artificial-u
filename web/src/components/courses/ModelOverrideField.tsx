import { type Component, createResource, For } from 'solid-js'
import type { ModelSettingResponse } from '../../api/services/preference-service'
import { SUGGESTED_MODELS } from '../../utils/models'
import { FormField, Input } from '../ui'

/** Optional model override input; blank means the configured default (shown as placeholder). */
const ModelOverrideField: Component<{
  name: string
  label: string
  helperText: string
  loadDefault: () => Promise<ModelSettingResponse>
  value: string | null | undefined
  onChange: (value: string | null) => void
  disabled?: boolean
}> = (props) => {
  const [defaultModel] = createResource(() => props.loadDefault().catch(() => null))
  const listId = () => `${props.name}-suggestions`

  return (
    <FormField label={props.label} name={props.name} helperText={props.helperText}>
      <Input
        name={props.name}
        list={listId()}
        value={props.value ?? ''}
        onChange={(v) => {
          props.onChange(v.trim() || null)
        }}
        placeholder={defaultModel()?.model ?? ''}
        disabled={props.disabled}
        type="text"
      />
      <datalist id={listId()}>
        <For each={SUGGESTED_MODELS}>{(model) => <option value={model} />}</For>
      </datalist>
    </FormField>
  )
}

export default ModelOverrideField
