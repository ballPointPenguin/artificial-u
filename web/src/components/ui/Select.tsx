import { Select as KSelect } from '@kobalte/core/select'
import type { ComponentProps, JSX } from '@solidjs/web'
import ChevronDown from 'lucide-solid/icons/chevron-down'
import type { Component } from 'solid-js'
import { omit, Show } from 'solid-js'

export interface SelectOption {
  value: string | number
  label: string | JSX.Element // Allow JSX for richer labels
  disabled?: boolean
}

// Omit props that are handled internally or have different signatures
interface SelectProps
  extends Omit<
    ComponentProps<typeof KSelect<SelectOption>>,
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
  const others = omit(
    props,
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
    'label'
  )

  const fieldId = () => `field-${props.name}`
  const hasError = () => !!props.error

  // Helper to find the full option object based on the primitive value
  const findOptionByValue = (val: SelectOption['value'] | null | undefined) => {
    if (val === null || val === undefined) return undefined
    return props.options.find((opt) => opt.value === val)
  }

  return (
    <KSelect<SelectOption>
      {...others}
      multiple={false} // Explicitly set to false for single selection
      options={props.options}
      optionValue="value"
      optionTextValue="label"
      optionDisabled="disabled"
      value={findOptionByValue(props.value)}
      onChange={(selectedOptionObject: SelectOption | null) => {
        // For single (multiple=false), onChange gives SelectOption | null
        if (props.onChange) {
          props.onChange(selectedOptionObject ? selectedOptionObject.value : null)
        }
      }}
      placeholder={props.placeholder || 'Select...'}
      validationState={hasError() ? 'invalid' : 'valid'}
      disabled={props.disabled}
      required={props.required}
      class={props.class}
      name={props.name}
      id={fieldId()}
      // Kobalte alpha itemComponent typing is incomplete relative to CollectionNode.
      itemComponent={(itemProps) => {
        const item = itemProps.item as {
          rawValue: SelectOption
        } & (typeof itemProps)['item']
        return (
          <KSelect.Item
            item={item}
            class={`flex justify-between items-center p-2 text-sm rounded-sm cursor-pointer
                    hover:bg-primary/10 data-[highlighted]:bg-primary/20 data-[selected]:bg-primary/30
                    data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed
                    ${props.itemClass || ''}`}
          >
            <KSelect.ItemLabel>{item.rawValue.label}</KSelect.ItemLabel>
            <KSelect.ItemIndicator class="ml-2 text-primary">✓</KSelect.ItemIndicator>
          </KSelect.Item>
        )
      }}
    >
      {/* Visually hidden label for accessibility if not using FormField */}
      <Show when={props.label && KSelect.Label}>
        <KSelect.Label class="sr-only" as="label" for={fieldId()}>
          {props.label}
        </KSelect.Label>
      </Show>

      <KSelect.Trigger
        class={`arcane-input flex items-center justify-between w-full appearance-none ${props.triggerClass || ''}`}
        aria-invalid={hasError() ? 'true' : 'false'}
        aria-describedby={
          hasError() ? `${fieldId()}-error ${fieldId()}-helper` : `${fieldId()}-helper`
        }
      >
        <KSelect.Value<SelectOption>>
          {(state) => {
            const selected = state.selectedOption() as SelectOption | undefined
            const label = selected?.label || props.placeholder || 'Select...'
            return <span class="truncate">{label}</span>
          }}
        </KSelect.Value>
        <KSelect.Icon class="ml-2">
          <ChevronDown size={16} class="opacity-75" />
        </KSelect.Icon>
      </KSelect.Trigger>

      <KSelect.Portal>
        <KSelect.Content
          class={`bg-surface text-foreground border border-border rounded-sm shadow-lg p-1 z-50 ${props.contentClass || ''}`}
        >
          {/* Listbox does not take itemComponent, it's rendered by Root based on options */}
          <KSelect.Listbox<SelectOption> class="max-h-60 overflow-y-auto text-foreground" />
        </KSelect.Content>
      </KSelect.Portal>
    </KSelect>
  )
}

export default Select
