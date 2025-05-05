import { For, Show, createResource } from 'solid-js'
import { getDepartments } from '../../api/services/department-service'
import { getProfessors } from '../../api/services/professor-service'
import { useCourseForm } from './FormContext'
import type { BasicInfoProps } from './types'

export function BasicInfo(props: BasicInfoProps) {
  const { form, errors, updateForm } = useCourseForm()

  // Fetch departments for dropdown
  const [departments] = createResource(() => getDepartments({ size: 100 }))

  // Fetch professors for dropdown
  const [professors] = createResource(() => getProfessors({ size: 100 }))

  const handleChange = (
    e: Event & {
      currentTarget: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    }
  ) => {
    const { name, value, type } = e.currentTarget
    updateForm(name, type === 'number' ? Number(value) : value)
  }

  return (
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Course Code */}
      <div>
        <label for="code" class="block text-sm font-medium mb-1 text-parchment-300">
          Course Code*
        </label>
        <input
          id="code"
          name="code"
          type="text"
          required
          value={form.code}
          onInput={handleChange}
          placeholder="e.g., CS101"
          class="arcane-input"
          classList={{
            'border-red-500': !!errors.code,
          }}
          disabled={props.disabled}
        />
        <Show when={errors.code}>
          <p class="mt-1 text-sm text-red-600">{errors.code}</p>
        </Show>
      </div>

      {/* Course Title */}
      <div>
        <label for="title" class="block text-sm font-medium mb-1 text-parchment-300">
          Course Title*
        </label>
        <input
          id="title"
          name="title"
          type="text"
          required
          value={form.title}
          onInput={handleChange}
          placeholder="Introduction to Computer Science"
          class="arcane-input"
          classList={{
            'border-red-500': !!errors.title,
          }}
          disabled={props.disabled}
        />
        <Show when={errors.title}>
          <p class="mt-1 text-sm text-red-600">{errors.title}</p>
        </Show>
      </div>

      {/* Department */}
      <div>
        <label for="department_id" class="block text-sm font-medium mb-1 text-parchment-300">
          Department*
        </label>
        <select
          id="department_id"
          name="department_id"
          required
          value={form.department_id || ''}
          onChange={handleChange}
          class="arcane-input"
          classList={{
            'border-red-500': !!errors.department_id,
          }}
          disabled={props.disabled || departments.loading}
        >
          <option value="">Select a department</option>
          <Show when={!departments.loading && departments()}>
            {(depts) => (
              <For each={depts().items}>
                {(dept) => (
                  <option value={dept.id}>
                    {dept.name} ({dept.code})
                  </option>
                )}
              </For>
            )}
          </Show>
        </select>
        <Show when={departments.loading}>
          <p class="text-parchment-400 text-sm mt-1">Loading departments...</p>
        </Show>
        <Show when={errors.department_id}>
          <p class="mt-1 text-sm text-red-600">{errors.department_id}</p>
        </Show>
      </div>

      {/* Professor */}
      <div>
        <label for="professor_id" class="block text-sm font-medium mb-1 text-parchment-300">
          Professor*
        </label>
        <select
          id="professor_id"
          name="professor_id"
          required
          value={form.professor_id || ''}
          onChange={handleChange}
          class="arcane-input"
          classList={{
            'border-red-500': !!errors.professor_id,
          }}
          disabled={props.disabled || professors.loading}
        >
          <option value="">Select a professor</option>
          <Show when={!professors.loading && professors()}>
            {(profs) => (
              <For each={profs().items}>
                {(prof) => (
                  <option value={prof.id}>
                    {prof.name} - {prof.title}
                  </option>
                )}
              </For>
            )}
          </Show>
        </select>
        <Show when={professors.loading}>
          <p class="text-parchment-400 text-sm mt-1">Loading professors...</p>
        </Show>
        <Show when={errors.professor_id}>
          <p class="mt-1 text-sm text-red-600">{errors.professor_id}</p>
        </Show>
      </div>

      {/* Course Level */}
      <div>
        <label for="level" class="block text-sm font-medium mb-1 text-parchment-300">
          Level*
        </label>
        <select
          id="level"
          name="level"
          required
          value={form.level}
          onChange={handleChange}
          class="arcane-input"
          disabled={props.disabled}
        >
          <option value="Undergraduate">Undergraduate</option>
          <option value="Graduate">Graduate</option>
          <option value="Doctoral">Doctoral</option>
          <option value="Certificate">Certificate</option>
        </select>
      </div>

      {/* Credits */}
      <div>
        <label for="credits" class="block text-sm font-medium mb-1 text-parchment-300">
          Credits*
        </label>
        <input
          id="credits"
          name="credits"
          type="number"
          min="0"
          max="12"
          required
          value={form.credits}
          onInput={handleChange}
          class="arcane-input"
          disabled={props.disabled}
        />
      </div>

      {/* Lectures Per Week */}
      <div>
        <label for="lectures_per_week" class="block text-sm font-medium mb-1 text-parchment-300">
          Lectures Per Week*
        </label>
        <input
          id="lectures_per_week"
          name="lectures_per_week"
          type="number"
          min="1"
          max="7"
          required
          value={form.lectures_per_week}
          onInput={handleChange}
          class="arcane-input"
          disabled={props.disabled}
        />
      </div>

      {/* Total Weeks */}
      <div>
        <label for="total_weeks" class="block text-sm font-medium mb-1 text-parchment-300">
          Total Weeks*
        </label>
        <input
          id="total_weeks"
          name="total_weeks"
          type="number"
          min="1"
          max="52"
          required
          value={form.total_weeks}
          onInput={handleChange}
          class="arcane-input"
          disabled={props.disabled}
        />
      </div>
    </div>
  )
}
