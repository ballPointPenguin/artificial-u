import { Select as KSelect } from '@kobalte/core'
import { ChevronDown } from 'lucide-solid'
import type { Component, ComponentProps, JSX } from 'solid-js'
import { Show, splitProps } from 'solid-js'

export interface SelectOption {
  value: string | number
  label: string | JSX.Element // Allow JSX for richer labels
  disabled?: boolean
}

// Omit props that are handled internally or have different signatures
interface SelectProps
  extends Omit<
    ComponentProps<typeof KSelect.Root<SelectOption>>,
    | 'value'
    | 'defaultValue'
    | 'onChange'
    | 'options'
    | 'itemComponent'
    | 'placeholder'
    | 'name'
    | 'id'
    | 'required'
    | 'disabled'
    | 'validationState'
    | 'multiple'
  > {
  name: string // Required for form association and fieldId
  label?: string // Optional: FormField will primarily handle the label
  error?: string | null | false
  value?: SelectOption['value'] | null // The primitive value
  onChange?: (value: SelectOption['value'] | null) => void // Event with the primitive value
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
  required?: boolean
  class?: string // For KSelect.Root
  triggerClass?: string
  contentClass?: string
  itemClass?: string
}

const Select: Component<SelectProps> = (props) => {
  const [local, others] = splitProps(props, [
    'name',
    'value',
    'onChange',
    'options',
    'placeholder',
    'disabled',
    'required',
    'class',
    'triggerClass',
    'contentClass',
    'itemClass',
    'error',
    'label',
  ])

  const fieldId = () => `field-${local.name}`
  const hasError = () => !!local.error

  // Helper to find the full option object based on the primitive value
  const findOptionByValue = (val: SelectOption['value'] | null | undefined) => {
    if (val === null || val === undefined) return undefined
    return local.options.find((opt) => opt.value === val)
  }

  return (
    <KSelect.Root<SelectOption>
      {...others}
      multiple={false} // Explicitly set to false for single selection
      options={local.options}
      optionValue="value"
      optionTextValue="label"
      optionDisabled="disabled"
      value={findOptionByValue(local.value)}
      onChange={(selectedOptionObject: SelectOption | null) => {
        // For single (multiple=false), onChange gives SelectOption | null
        if (local.onChange) {
          local.onChange(selectedOptionObject ? selectedOptionObject.value : null)
        }
      }}
      placeholder={local.placeholder || 'Select...'}
      validationState={hasError() ? 'invalid' : 'valid'}
      disabled={local.disabled}
      required={local.required}
      class={local.class}
      name={local.name}
      id={fieldId()}
      itemComponent={(itemProps) => {
        // itemProps is KSelect.SelectItemState<SelectOption>
        // itemProps.item is the CollectionNode<SelectOption>
        // itemProps.item.rawValue is the SelectOption object
        return (
          <KSelect.Item
            item={itemProps.item} // Pass the CollectionNode itself
            class={`flex justify-between items-center p-2 text-sm rounded-sm cursor-pointer
                    hover:bg-primary/10 data-[highlighted]:bg-primary/20 data-[selected]:bg-primary/30
                    data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed
                    ${local.itemClass || ''}`}
          >
            {/* Access rawValue for display purposes */}
            <KSelect.ItemLabel>{itemProps.item.rawValue.label}</KSelect.ItemLabel>
            <KSelect.ItemIndicator class="ml-2 text-primary">✓</KSelect.ItemIndicator>
          </KSelect.Item>
        )
      }}
    >
      {/* Visually hidden label for accessibility if not using FormField */}
      <Show when={local.label && KSelect.Label}>
        <KSelect.Label class="sr-only" as="label" for={fieldId()}>
          {local.label}
        </KSelect.Label>
      </Show>

      <KSelect.Trigger
        class={`arcane-input flex items-center justify-between w-full appearance-none ${local.triggerClass || ''}`}
        aria-invalid={hasError()}
        aria-describedby={
          hasError() ? `${fieldId()}-error ${fieldId()}-helper` : `${fieldId()}-helper`
        }
      >
        <KSelect.Value<SelectOption>>
          {(state) =>
            state.selectedOption().label || (
              <span class="text-muted">{local.placeholder || 'Select...'}</span>
            )
          }
        </KSelect.Value>
        <KSelect.Icon class="ml-2">
          <ChevronDown size={16} class="opacity-75" />
        </KSelect.Icon>
      </KSelect.Trigger>

      <KSelect.Portal>
        <KSelect.Content
          class={`bg-surface border border-border rounded-sm shadow-lg p-1 z-50 ${local.contentClass || ''}`}
        >
          {/* Listbox does not take itemComponent, it's rendered by Root based on options */}
          <KSelect.Listbox<SelectOption> class="max-h-60 overflow-y-auto" />
        </KSelect.Content>
      </KSelect.Portal>
    </KSelect.Root>
  )
}

export default Select
