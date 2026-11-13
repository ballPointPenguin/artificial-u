import { type Component, createResource, For } from 'solid-js'
import { preferenceService } from '../../api/services/preference-service'
import { useTranslations } from '../../i18n'
import { SUGGESTED_MODELS } from '../../utils/models'
import { FormField, Input } from '../ui'

/** Optional per-course lecture model override; blank means the app default is used. */
const LectureModelField: Component<{
  value: string | null | undefined
  onChange: (value: string | null) => void
  disabled?: boolean
}> = (props) => {
  const t = useTranslations()
  const [appDefault] = createResource(() =>
    preferenceService.getLectureGenerationModel().catch(() => null)
  )

  return (
    <FormField
      label={t().courses.form.lectureModelLabel}
      name="lecture_generation_model"
      helperText={t().courses.form.lectureModelHelper}
    >
      <Input
        name="lecture_generation_model"
        list="lecture-model-suggestions"
        value={props.value ?? ''}
        onChange={(v) => {
          props.onChange(v.trim() || null)
        }}
        placeholder={appDefault()?.model ?? ''}
        disabled={props.disabled}
        type="text"
      />
      <datalist id="lecture-model-suggestions">
        <For each={SUGGESTED_MODELS}>{(model) => <option value={model} />}</For>
      </datalist>
    </FormField>
  )
}

export default LectureModelField
