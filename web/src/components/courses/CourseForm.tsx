import type { Component } from 'solid-js'
import { createEffect, createMemo, createResource, createSignal, For, Show } from 'solid-js'
import { courseService } from '../../api/services/course-service.js'
import { departmentService } from '../../api/services/department-service.js'
import { professorService } from '../../api/services/professor-service.js'
import type { Course, CourseGenerateRequest, Department, Professor } from '../../api/types.js'
import { useAuth } from '../../auth/AuthProvider.js'
import { useContentLanguage, useTranslations } from '../../i18n'
import { TopicContentRenderer } from '../topics/TopicContentRenderer.jsx'
import {
  Alert,
  Button,
  Form,
  FormActions,
  FormField,
  Input,
  MagicButton,
  Select,
  Textarea,
} from '../ui'
import type { SelectOption } from '../ui/Select.js'
import ConnectedCoursesSelect from './ConnectedCoursesSelect.jsx'
import LectureModelField from './LectureModelField.jsx'
import type { CourseFormData } from './types.js'

interface CourseFormProps {
  course?: Course // For editing
  onSubmit: (data: CourseFormData) => Promise<void>
  onCancel: () => void
  isSubmitting: boolean
  error?: string
  setError?: (error: string) => void
}

const CourseForm: Component<CourseFormProps> = (props) => {
  const auth = useAuth()
  const t = useTranslations()
  const { contentLanguage } = useContentLanguage()

  const [formData, setFormData] = createSignal<CourseFormData>({
    code: '',
    title: '',
    department_id: null,
    connected_course_ids: [],
    level: null,
    professor_id: null,
    description: '',
    notes: null,
    lecture_generation_model: null,
    lectures_per_week: null,
    total_weeks: null,
    topics: [],
    freeform_prompt: '',
    created_with: null,
  })

  const [validationErrors, setValidationErrors] = createSignal<Record<string, string>>({})
  const [isGenerating, setIsGenerating] = createSignal(false)
  const [generateError, setGenerateError] = createSignal<string | null>(null)
  const [hasGeneratedDraft, setHasGeneratedDraft] = createSignal(false)
  const [isManualMode, setIsManualMode] = createSignal(false)
  const [showAdvanced, setShowAdvanced] = createSignal(false)
  const [refinePrompt, setRefinePrompt] = createSignal('')
  const [isSyllabusExpanded, setIsSyllabusExpanded] = createSignal(false)

  const isEditMode = () => props.course !== undefined
  const showFullForm = () => isEditMode() || hasGeneratedDraft() || isManualMode()

  // Populate form for editing
  createEffect(() => {
    const c = props.course
    if (c) {
      setFormData({
        code: c.code || '',
        title: c.title || '',
        department_id: c.department_id,
        connected_course_ids: c.connected_course_ids,
        level: c.level || '',
        professor_id: c.professor_id,
        description: c.description || '',
        notes: c.notes || null,
        lecture_generation_model: c.settings?.lecture_generation_model ?? null,
        lectures_per_week: c.lectures_per_week,
        total_weeks: c.total_weeks,
        freeform_prompt: '', // Reset generate prompt on edit
      })
    }
  })

  // Handle resource errors in tracked scopes
  createEffect(() => {
    const depError: unknown = departmentsResource.error
    if (depError) {
      props.setError?.(t().courses.form.failedToLoadDepartments)
    }
  })

  createEffect(() => {
    const profError: unknown = professorsResource.error
    if (profError) {
      props.setError?.(t().courses.form.failedToLoadProfessors)
    }
  })

  // Sentinel value for null option (IDs are positive integers, so -1 is safe)
  const NULL_OPTION_VALUE = -1

  // Level options for the dropdown (computed to pick up locale changes)
  const levelOptions = (): SelectOption[] => [
    { value: NULL_OPTION_VALUE, label: t().courses.form.levelPlaceholder },
    { value: 'Undergraduate', label: t().courses.form.levelUndergraduate },
    { value: 'Graduate', label: t().courses.form.levelGraduate },
  ]

  // Fetch departments for Select
  const [departmentsResource] = createResource(contentLanguage, async (lang) => {
    try {
      const response = await departmentService.listDepartments({
        page: 1,
        size: 100,
        language: lang,
      })
      const departmentOptions = response.items.map((dept: Department) => ({
        value: dept.id,
        label: `${dept.name} (${dept.code})`,
      })) as SelectOption[]
      // Add null option at the beginning to allow unselection
      return [
        { value: NULL_OPTION_VALUE, label: t().courses.form.departmentPlaceholder },
        ...departmentOptions,
      ] as SelectOption[]
    } catch {
      // Don't access reactive props inside async functions
      // Let the component handle the error state through resource.error
      throw new Error('Failed to load departments')
    }
  })

  // Fetch professors for Select, filtered by department and language.
  // A combined string key is used so both signals trigger refetch without
  // causing the infinite-loop that object sources produce (new ref each render).
  const [professorsResource] = createResource(
    () => `${String(formData().department_id ?? '')}_${contentLanguage()}`,
    async (key) => {
      const sepIdx = key.lastIndexOf('_')
      const lang = key.slice(sepIdx + 1)
      const deptIdStr = key.slice(0, sepIdx)
      const departmentId = deptIdStr ? Number(deptIdStr) : null
      try {
        const response = await professorService.listProfessors({
          page: 1,
          size: 100,
          language: lang,
          ...(departmentId ? { departmentId } : {}),
        })
        const professorOptions = response.items.map((prof: Professor) => ({
          value: prof.id,
          label: prof.name || 'Unnamed Professor',
        })) as SelectOption[]
        // Add null option at the beginning to allow unselection
        return [
          { value: NULL_OPTION_VALUE, label: t().courses.form.professorPlaceholder },
          ...professorOptions,
        ] as SelectOption[]
      } catch {
        // Don't access reactive props inside async functions
        // Let the component handle the error state through resource.error
        throw new Error('Failed to load professors')
      }
    }
  )

  const [departmentCoursesResource] = createResource(
    () => ({
      departmentId: formData().department_id,
      // Refetch once auth is ready so include_hidden uses the JWT student context
      authReady: !auth.isLoading(),
      excludeCourseId: props.course?.id,
    }),
    async ({ departmentId, excludeCourseId }) => {
      if (!departmentId) return [] as Course[]
      const response = await courseService.listCourses({
        page: 1,
        size: 100,
        departmentId,
        // Published plus own hidden courses (or all hidden for admins). This matches
        // what the API lets this user newly connect; connections to other hidden
        // courses are preserved but not shown (see handleConnectedCoursesChange).
        includeHidden: true,
      })
      return response.items.filter((course) => course.id !== excludeCourseId)
    }
  )

  const visibleConnectedCourseIds = createMemo(() => {
    const availableIds = new Set((departmentCoursesResource() || []).map((course) => course.id))
    return formData().connected_course_ids.filter((id) => availableIds.has(id))
  })

  const handleConnectedCoursesChange = (selectedIds: number[]) => {
    const availableIds = new Set((departmentCoursesResource() || []).map((course) => course.id))
    const preservedHiddenIds = formData().connected_course_ids.filter((id) => !availableIds.has(id))
    setFormData((prev) => ({
      ...prev,
      connected_course_ids: [...preservedHiddenIds, ...selectedIds],
    }))
  }

  const handleInputChange = (fieldName: keyof CourseFormData, value: string | number | null) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }))

    // When input changes, clear the specific validation error for that field
    if (validationErrors()[fieldName]) {
      setValidationErrors((prev) => {
        const newErrors: Record<string, string> = {}
        for (const key in prev) {
          if (key !== fieldName) {
            newErrors[key] = prev[key]
          }
        }
        return newErrors
      })
    }
  }

  const validateForm = (data: CourseFormData): boolean => {
    const errors: Record<string, string> = {}
    if (!data.code.trim()) errors.code = t().courses.form.codeRequired
    if (!data.title.trim()) errors.title = t().courses.form.titleRequired
    // department_id, professor_id, and level are now optional - no validation needed
    if (!data.description.trim()) errors.description = t().courses.form.descriptionRequired
    // Optional fields like lectures_per_week, total_weeks can be validated if they have specific rules when provided
    if (data.lectures_per_week !== null) {
      if (Number(data.lectures_per_week) < 1 || Number(data.lectures_per_week) > 5) {
        errors.lectures_per_week = t().courses.form.lecturesPerWeekRange
      }
    }
    if (data.total_weeks !== null) {
      if (Number(data.total_weeks) < 1 || Number(data.total_weeks) > 50) {
        errors.total_weeks = t().courses.form.totalWeeksRange
      }
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = () => {
    if (validateForm(formData())) {
      void props.onSubmit(formData()) // Parent will handle mapping to Create/Update payload
    }
  }

  const handleGenerate = async (isRefinement = false) => {
    const currentData = formData()
    const activePrompt = (isRefinement ? refinePrompt() : currentData.freeform_prompt || '').trim()

    if (
      !showFullForm() &&
      !activePrompt &&
      !currentData.title.trim() &&
      !currentData.description.trim()
    ) {
      setGenerateError(t().courses.form.promptOrTitleRequired)
      return
    }

    setIsGenerating(true)
    setGenerateError(null)
    setValidationErrors({}) // Clear validation before generation

    const partialAttributes: Record<string, unknown> = {
      ...(currentData.code && { code: currentData.code }),
      ...(currentData.title && { title: currentData.title }),
      ...(currentData.department_id && { department_id: currentData.department_id }),
      ...(currentData.professor_id && { professor_id: currentData.professor_id }),
      ...(currentData.level && { level: currentData.level }),
      ...(currentData.description && { description: currentData.description }),
      ...(currentData.notes && { notes: currentData.notes }),
      ...(currentData.lectures_per_week && { lectures_per_week: currentData.lectures_per_week }),
      ...(currentData.total_weeks && { total_weeks: currentData.total_weeks }),
      language: contentLanguage(),
      ...(isRefinement &&
        currentData.topics &&
        currentData.topics.length > 0 && { topics: currentData.topics }),
    }

    const payload: CourseGenerateRequest = {
      partial_attributes: partialAttributes,
      ...(activePrompt && { freeform_prompt: activePrompt }),
      ...(currentData.connected_course_ids.length > 0 && {
        connected_course_ids: currentData.connected_course_ids,
      }),
    }

    try {
      const generated = await courseService.generateCourse(payload)
      setFormData((prev) => ({
        ...prev,
        code: generated.code || prev.code,
        title: generated.title || prev.title,
        department_id: generated.department_id,
        level: generated.level || prev.level,
        professor_id: generated.professor_id,
        description: generated.description || prev.description,
        notes: generated.notes || prev.notes,
        lectures_per_week: generated.lectures_per_week,
        total_weeks: generated.total_weeks,
        topics: Array.isArray(generated.topics) ? generated.topics : prev.topics,
        created_with: generated.created_with || prev.created_with,
        connected_course_ids: Array.isArray(generated.connected_course_ids)
          ? generated.connected_course_ids
          : prev.connected_course_ids,
      }))
      setHasGeneratedDraft(true)
      if (isRefinement) {
        setRefinePrompt('')
      }
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : t().courses.form.failedToGenerate)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleClear = () => {
    setFormData({
      code: '',
      title: '',
      department_id: null,
      connected_course_ids: [],
      level: null,
      professor_id: null,
      description: '',
      notes: null,
      lecture_generation_model: null,
      lectures_per_week: null,
      total_weeks: null,
      topics: [],
      freeform_prompt: '',
      created_with: null,
    })
    setRefinePrompt('')
    setHasGeneratedDraft(false)
    setValidationErrors({})
    setGenerateError(null)
  }

  const isDisabled = () => props.isSubmitting || isGenerating()

  return (
    <Form onSubmit={handleSubmit}>
      <Show
        when={showFullForm()}
        fallback={
          <>
            <FormField
              label={t().courses.form.syllabusPromptLabel}
              name="freeform_prompt"
              helperText={t().courses.form.syllabusPromptHelper}
              error={validationErrors().freeform_prompt}
            >
              <Textarea
                name="freeform_prompt"
                rows={4}
                placeholder={t().courses.form.syllabusPromptPlaceholder}
                value={formData().freeform_prompt || ''}
                onChange={(v) => {
                  handleInputChange('freeform_prompt', v)
                }}
                disabled={isDisabled()}
              />
            </FormField>

            <div class="my-4 border border-parchment-700/40 rounded-lg bg-obsidian-900/20">
              <button
                type="button"
                class="w-full flex items-center justify-between px-4 py-3 text-left font-serif text-sm text-parchment-200 hover:text-parchment-100 transition-colors cursor-pointer"
                onClick={() => {
                  setShowAdvanced((prev) => !prev)
                }}
              >
                <span>{t().courses.form.advancedOptions}</span>
                <span class="text-xs text-parchment-400">{showAdvanced() ? '▲' : '▼'}</span>
              </button>

              <Show when={showAdvanced()}>
                <div class="px-4 pb-4 pt-2 border-t border-parchment-700/30 space-y-4">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                    <FormField
                      label={t().courses.form.departmentLabel}
                      name="department_id"
                      error={validationErrors().department_id}
                      helperText={
                        formData().department_id === null
                          ? t().courses.form.aiDeterminesDepartment
                          : undefined
                      }
                    >
                      <Select
                        name="department_id"
                        options={departmentsResource() || []}
                        value={
                          formData().department_id === null
                            ? NULL_OPTION_VALUE
                            : formData().department_id
                        }
                        onChange={(v) => {
                          const departmentId =
                            v === NULL_OPTION_VALUE || v === null || v === '' ? null : Number(v)
                          if (departmentId === formData().department_id) return
                          handleInputChange('department_id', departmentId)
                          setFormData((prev) => ({
                            ...prev,
                            professor_id: null,
                            connected_course_ids: [],
                          }))
                        }}
                        placeholder={t().courses.form.departmentPlaceholder}
                        disabled={departmentsResource.loading || isDisabled()}
                      />
                    </FormField>
                    {formData().department_id !== null ? (
                      <FormField
                        label={t().courses.form.connectedCourses}
                        name="connected_course_ids"
                        helperText={t().courses.form.connectedCoursesHelper}
                      >
                        <ConnectedCoursesSelect
                          courses={departmentCoursesResource() || []}
                          value={visibleConnectedCourseIds()}
                          onChange={handleConnectedCoursesChange}
                          disabled={departmentCoursesResource.loading || isDisabled()}
                        />
                      </FormField>
                    ) : null}
                    <FormField
                      label={t().courses.form.professorLabel}
                      name="professor_id"
                      error={validationErrors().professor_id}
                      helperText={
                        formData().professor_id === null
                          ? t().courses.form.aiDeterminesProfessor
                          : undefined
                      }
                    >
                      <Select
                        name="professor_id"
                        options={professorsResource() || []}
                        value={
                          formData().professor_id === null
                            ? NULL_OPTION_VALUE
                            : formData().professor_id
                        }
                        onChange={(v) => {
                          const professorId =
                            v === NULL_OPTION_VALUE || v === null || v === '' ? null : Number(v)
                          handleInputChange('professor_id', professorId)
                        }}
                        placeholder={t().courses.form.professorPlaceholder}
                        disabled={professorsResource.loading || isDisabled()}
                      />
                    </FormField>
                    <FormField
                      label={t().courses.form.levelLabel}
                      name="level"
                      error={validationErrors().level}
                      helperText={
                        !formData().level ? t().courses.form.aiDeterminesLevel : undefined
                      }
                    >
                      <Select
                        name="level"
                        options={levelOptions()}
                        value={formData().level || NULL_OPTION_VALUE}
                        onChange={(v) => {
                          const level = v === NULL_OPTION_VALUE ? null : String(v)
                          handleInputChange('level', level)
                        }}
                        placeholder={t().courses.form.levelPlaceholder}
                        disabled={isDisabled()}
                      />
                    </FormField>
                    <FormField
                      label={t().courses.form.lecturesPerWeekLabel}
                      name="lectures_per_week"
                      error={validationErrors().lectures_per_week}
                      helperText={t().courses.form.lecturesPerWeekHelper}
                    >
                      <Input
                        name="lectures_per_week"
                        type="number"
                        min={1}
                        max={5}
                        value={formData().lectures_per_week ?? ''}
                        onChange={(v) => {
                          handleInputChange('lectures_per_week', v === '' ? null : Number(v))
                        }}
                        disabled={isDisabled()}
                      />
                    </FormField>
                    <FormField
                      label={t().courses.form.totalWeeksLabel}
                      name="total_weeks"
                      error={validationErrors().total_weeks}
                      helperText={t().courses.form.totalWeeksHelper}
                    >
                      <Input
                        name="total_weeks"
                        type="number"
                        min={1}
                        max={50}
                        value={formData().total_weeks ?? ''}
                        onChange={(v) => {
                          handleInputChange('total_weeks', v === '' ? null : Number(v))
                        }}
                        disabled={isDisabled()}
                      />
                    </FormField>
                    <FormField
                      label={t().courses.form.codeLabel}
                      name="code"
                      error={validationErrors().code}
                    >
                      <Input
                        name="code"
                        value={formData().code}
                        onChange={(v) => {
                          handleInputChange('code', v)
                        }}
                        disabled={isDisabled()}
                      />
                    </FormField>
                    <FormField
                      label={t().courses.form.titleLabel}
                      name="title"
                      error={validationErrors().title}
                    >
                      <Input
                        name="title"
                        value={formData().title}
                        onChange={(v) => {
                          handleInputChange('title', v)
                        }}
                        disabled={isDisabled()}
                      />
                    </FormField>
                  </div>

                  <FormField
                    label={t().courses.form.notesLabel}
                    name="notes"
                    helperText={t().courses.form.notesHelper}
                    error={validationErrors().notes}
                  >
                    <Textarea
                      name="notes"
                      rows={2}
                      placeholder={t().courses.form.notesPlaceholder}
                      value={formData().notes || ''}
                      onChange={(v) => {
                        handleInputChange('notes', v || null)
                      }}
                      disabled={isDisabled()}
                    />
                  </FormField>

                  <LectureModelField
                    value={formData().lecture_generation_model}
                    onChange={(v) => {
                      handleInputChange('lecture_generation_model', v)
                    }}
                    disabled={isDisabled()}
                  />
                </div>
              </Show>
            </div>

            <div class="mb-2 flex justify-end">
              <button
                type="button"
                class="text-xs font-serif text-parchment-400 hover:text-parchment-200 underline cursor-pointer"
                onClick={() => {
                  setIsManualMode(true)
                }}
                disabled={isDisabled()}
              >
                {t().courses.form.fillManuallyInstead}
              </button>
            </div>

            <Show when={props.error || generateError()}>
              <Alert variant="danger" class="my-4">
                {props.error || generateError()}
              </Alert>
            </Show>

            <FormActions>
              <Button
                type="button"
                variant="outline"
                onClick={props.onCancel}
                disabled={isDisabled()}
              >
                {t().common.cancel}
              </Button>
              <Button type="button" variant="outline" onClick={handleClear} disabled={isDisabled()}>
                {t().common.clear}
              </Button>
              <MagicButton
                type="button"
                variant="primary"
                onClick={() => {
                  void handleGenerate(false)
                }}
                disabled={isDisabled()}
                isLoading={isGenerating()}
                loadingText={t().courses.form.generatingSyllabus}
              >
                {t().courses.form.generateSyllabus}
              </MagicButton>
            </FormActions>
          </>
        }
      >
        <Show when={!isEditMode() && !hasGeneratedDraft() && isManualMode()}>
          <div class="mb-4 flex justify-end">
            <button
              type="button"
              class="text-xs font-serif text-parchment-400 hover:text-parchment-200 underline cursor-pointer"
              onClick={() => {
                setIsManualMode(false)
              }}
              disabled={isDisabled()}
            >
              {t().courses.form.usePromptBuilderInstead}
            </button>
          </div>
        </Show>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          <FormField
            label={t().courses.form.codeLabel}
            name="code"
            required
            error={validationErrors().code}
          >
            <Input
              name="code"
              value={formData().code}
              onChange={(v) => {
                handleInputChange('code', v)
              }}
              disabled={isDisabled()}
              required
            />
          </FormField>
          <FormField
            label={t().courses.form.titleLabel}
            name="title"
            required
            error={validationErrors().title}
          >
            <Input
              name="title"
              value={formData().title}
              onChange={(v) => {
                handleInputChange('title', v)
              }}
              disabled={isDisabled()}
              required
            />
          </FormField>
          <FormField
            label={t().courses.form.departmentLabel}
            name="department_id"
            error={validationErrors().department_id}
            helperText={
              formData().department_id === null
                ? t().courses.form.aiDeterminesDepartment
                : undefined
            }
          >
            <Select
              name="department_id"
              options={departmentsResource() || []}
              value={
                formData().department_id === null ? NULL_OPTION_VALUE : formData().department_id
              }
              onChange={(v) => {
                // Convert sentinel value to null, otherwise use the selected value
                const departmentId =
                  v === NULL_OPTION_VALUE || v === null || v === '' ? null : Number(v)
                // Guard: Kobalte fires onChange when the controlled value prop changes
                // programmatically (e.g. when createEffect populates the form from
                // props.course). In that case formData is already up-to-date and we
                // must NOT clear the professor that was just populated.
                if (departmentId === formData().department_id) return
                handleInputChange('department_id', departmentId)
                // Clear professor selection when department changes to avoid mismatch
                setFormData((prev) => ({
                  ...prev,
                  professor_id: null,
                  ...(props.course ? {} : { connected_course_ids: [] }),
                }))
              }}
              placeholder={t().courses.form.departmentPlaceholder}
              disabled={departmentsResource.loading || isDisabled()}
            />
          </FormField>
          {formData().department_id !== null ? (
            <FormField
              label={t().courses.form.connectedCourses}
              name="connected_course_ids"
              helperText={t().courses.form.connectedCoursesHelper}
            >
              <ConnectedCoursesSelect
                courses={departmentCoursesResource() || []}
                value={visibleConnectedCourseIds()}
                onChange={handleConnectedCoursesChange}
                disabled={departmentCoursesResource.loading || isDisabled()}
              />
            </FormField>
          ) : null}
          <FormField
            label={t().courses.form.professorLabel}
            name="professor_id"
            error={validationErrors().professor_id}
            helperText={
              formData().professor_id === null ? t().courses.form.aiDeterminesProfessor : undefined
            }
          >
            <Select
              name="professor_id"
              options={professorsResource() || []}
              value={formData().professor_id === null ? NULL_OPTION_VALUE : formData().professor_id}
              onChange={(v) => {
                // Convert sentinel value to null, otherwise use the selected value
                const professorId =
                  v === NULL_OPTION_VALUE || v === null || v === '' ? null : Number(v)
                handleInputChange('professor_id', professorId)
              }}
              placeholder={t().courses.form.professorPlaceholder}
              disabled={professorsResource.loading || isDisabled()}
            />
          </FormField>
          <FormField
            label={t().courses.form.levelLabel}
            name="level"
            error={validationErrors().level}
            helperText={!formData().level ? t().courses.form.aiDeterminesLevel : undefined}
          >
            <Select
              name="level"
              options={levelOptions()}
              value={formData().level || NULL_OPTION_VALUE}
              onChange={(v) => {
                // Convert sentinel value to null, otherwise use the selected string value
                const level = v === NULL_OPTION_VALUE ? null : String(v)
                handleInputChange('level', level)
              }}
              placeholder={t().courses.form.levelPlaceholder}
              disabled={isDisabled()}
            />
          </FormField>
          <FormField
            label={t().courses.form.lecturesPerWeekLabel}
            name="lectures_per_week"
            error={validationErrors().lectures_per_week}
            helperText={t().courses.form.lecturesPerWeekHelper}
          >
            <Input
              name="lectures_per_week"
              type="number"
              min={1}
              max={5}
              value={formData().lectures_per_week ?? ''}
              onChange={(v) => {
                handleInputChange('lectures_per_week', v === '' ? null : Number(v))
              }}
              disabled={isDisabled()}
            />
          </FormField>
          <FormField
            label={t().courses.form.totalWeeksLabel}
            name="total_weeks"
            error={validationErrors().total_weeks}
            helperText={t().courses.form.totalWeeksHelper}
          >
            <Input
              name="total_weeks"
              type="number"
              min={1}
              max={50}
              value={formData().total_weeks ?? ''}
              onChange={(v) => {
                handleInputChange('total_weeks', v === '' ? null : Number(v))
              }}
              disabled={isDisabled()}
            />
          </FormField>
        </div>

        <FormField
          label={t().courses.form.descriptionLabel}
          name="description"
          required
          error={validationErrors().description}
        >
          <Textarea
            name="description"
            rows={4}
            value={formData().description}
            onChange={(v) => {
              handleInputChange('description', v)
            }}
            disabled={isDisabled()}
            required
          />
        </FormField>

        <FormField
          label={t().courses.form.notesLabel}
          name="notes"
          helperText={t().courses.form.notesHelper}
          error={validationErrors().notes}
        >
          <Textarea
            name="notes"
            rows={3}
            placeholder={t().courses.form.notesPlaceholder}
            value={formData().notes || ''}
            onChange={(v) => {
              handleInputChange('notes', v || null)
            }}
            disabled={isDisabled()}
          />
        </FormField>

        <LectureModelField
          value={formData().lecture_generation_model}
          onChange={(v) => {
            handleInputChange('lecture_generation_model', v)
          }}
          disabled={isDisabled()}
        />

        <Show
          when={(formData().topics?.length ?? 0) > 0}
          fallback={
            <FormField
              label={t().courses.form.aiPromptLabel}
              name="freeform_prompt"
              helperText={t().courses.form.aiPromptHelper}
              error={validationErrors().freeform_prompt}
            >
              <Textarea
                name="freeform_prompt"
                rows={3}
                value={formData().freeform_prompt || ''}
                onChange={(v) => {
                  handleInputChange('freeform_prompt', v)
                }}
                disabled={isDisabled()}
              />
            </FormField>
          }
        >
          <div class="my-6 space-y-3">
            <div class="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
              <div>
                <h3 class="text-lg font-display text-parchment-100">
                  {t().courses.form.syllabusPreviewTitle} ({formData().topics?.length ?? 0})
                </h3>
                <p class="text-sm font-serif text-parchment-400">
                  {t().courses.form.syllabusPreviewHelper}
                </p>
              </div>
              <button
                type="button"
                class="self-start sm:self-auto text-xs font-serif text-mystic-300 hover:text-mystic-200 underline whitespace-nowrap cursor-pointer"
                onClick={() => {
                  setIsSyllabusExpanded((prev) => !prev)
                }}
              >
                {isSyllabusExpanded()
                  ? t().courses.form.collapseSyllabus
                  : t().courses.form.expandSyllabus}
              </button>
            </div>
            <div
              class={`rounded-lg border border-parchment-600/60 bg-obsidian-950/35 p-3 space-y-3 ${
                isSyllabusExpanded()
                  ? 'overflow-visible'
                  : 'h-[28rem] min-h-48 max-h-[80vh] overflow-y-scroll resize-y'
              }`}
            >
              <For each={formData().topics}>
                {(topic) => (
                  <div class="p-4 rounded-lg border border-parchment-700/40 bg-obsidian-900/30">
                    <div class="flex items-baseline justify-between gap-2">
                      <h4 class="font-display text-base text-parchment-100">{topic.title}</h4>
                      <span class="text-xs font-serif text-mystic-300 whitespace-nowrap">
                        {t().courseDetail.week} {topic.week}
                        {(formData().lectures_per_week ?? 1) > 1
                          ? ` • #${String(topic.order)}`
                          : ''}
                      </span>
                    </div>
                    <TopicContentRenderer content={topic.content ?? null} class="mt-2 text-sm" />
                  </div>
                )}
              </For>
            </div>
          </div>

          <FormField
            label={t().courses.form.refinePromptLabel}
            name="refine_prompt"
            helperText={t().courses.form.refinePromptHelper}
          >
            <Textarea
              name="refine_prompt"
              rows={3}
              placeholder={t().courses.form.refinePromptPlaceholder}
              value={refinePrompt()}
              onChange={(v) => {
                setRefinePrompt(v)
              }}
              disabled={isDisabled()}
            />
          </FormField>
        </Show>

        {/* Display errors */}
        <Show when={props.error || generateError()}>
          <Alert variant="danger" class="my-4">
            {props.error || generateError()}
          </Alert>
        </Show>

        <FormActions>
          <Button type="button" variant="outline" onClick={props.onCancel} disabled={isDisabled()}>
            {t().common.cancel}
          </Button>
          <Button type="button" variant="outline" onClick={handleClear} disabled={isDisabled()}>
            {t().common.clear}
          </Button>
          <MagicButton
            type="button"
            variant="secondary"
            onClick={() => {
              void handleGenerate((formData().topics?.length ?? 0) > 0)
            }}
            disabled={isDisabled()}
            isLoading={isGenerating()}
            loadingText={
              (formData().topics?.length ?? 0) > 0
                ? t().courses.form.refiningSyllabus
                : t().common.generating
            }
          >
            {(formData().topics?.length ?? 0) > 0
              ? t().courses.form.refineSyllabus
              : t().courses.form.generateDetails}
          </MagicButton>
          <Button type="submit" variant="primary" disabled={isDisabled()}>
            {props.isSubmitting
              ? t().common.saving
              : props.course !== undefined
                ? t().courses.form.updateCourse
                : t().courses.form.saveCourse}
          </Button>
        </FormActions>
      </Show>
    </Form>
  )
}

export default CourseForm
