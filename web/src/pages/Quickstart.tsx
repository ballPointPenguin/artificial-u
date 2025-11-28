import { useNavigate } from '@solidjs/router'
import type { Component } from 'solid-js'
import { createSignal, Match, onMount, Switch } from 'solid-js'
import { quickstartService } from '../api/services/quickstart-service.js'
import type { QuickstartProfessorDetail, QuickstartStartResponse } from '../api/types.js'
import { IntentStep } from '../components/quickstart/IntentStep.jsx'
import { ProfessorStep } from '../components/quickstart/ProfessorStep.jsx'
import { StepIndicator } from '../components/quickstart/StepIndicator.jsx'
import { useI18n } from '../i18n/index.js'

type WizardStep = 'intent' | 'professor' | 'complete'

interface QuickstartState {
  step: WizardStep
  query: string
  courseId: number | null
  professorId: number | null
  departmentId: number | null
  courseTitle: string
  courseCode: string
  professor: QuickstartProfessorDetail | null
}

const STORAGE_KEY = 'quickstart_state'

const getInitialState = (): QuickstartState => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored) as QuickstartState
    }
  } catch (e) {
    console.error('Error reading quickstart state:', e)
  }
  return {
    step: 'intent',
    query: '',
    courseId: null,
    professorId: null,
    departmentId: null,
    courseTitle: '',
    courseCode: '',
    professor: null,
  }
}

const saveState = (state: QuickstartState) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (e) {
    console.error('Error saving quickstart state:', e)
  }
}

const clearState = () => {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (e) {
    console.error('Error clearing quickstart state:', e)
  }
}

const Quickstart: Component = () => {
  const { t } = useI18n()
  const navigate = useNavigate()
  const [state, setState] = createSignal<QuickstartState>(getInitialState())
  const [isLoading, setIsLoading] = createSignal(false)
  const [error, setError] = createSignal('')

  // Save state whenever it changes
  const updateState = (updates: Partial<QuickstartState>) => {
    setState((prev) => {
      const newState = { ...prev, ...updates }
      saveState(newState)
      return newState
    })
  }

  // Get current step number for indicator
  const currentStepNumber = () => {
    const step = state().step
    if (step === 'intent') return 1
    if (step === 'professor') return 2
    return 3
  }

  // Handle course generation (from Intent step)
  const handleCourseGenerate = async (query: string) => {
    setIsLoading(true)
    setError('')

    try {
      // Start the quickstart flow - creates course with smart selection
      const result: QuickstartStartResponse = await quickstartService.start({ query })

      // Fetch professor details
      const professorResponse = await quickstartService.getProfessor(
        result.professor_id,
        result.course_id
      )

      updateState({
        step: 'professor',
        query,
        courseId: result.course_id,
        professorId: result.professor_id,
        departmentId: result.department_id,
        courseTitle: result.course_title,
        courseCode: result.course_code,
        professor: professorResponse.professor,
      })
    } catch (err) {
      console.error('Error starting quickstart:', err)
      setError(t().quickstart.errors.failedToCreateCourse)
    } finally {
      setIsLoading(false)
    }
  }

  // Handle professor acceptance
  const handleProfessorAccept = async () => {
    const currentState = state()
    if (!currentState.courseId) return

    setIsLoading(true)
    setError('')

    try {
      // Finalize the quickstart - kicks off topic and lecture generation
      await quickstartService.finalize({ course_id: currentState.courseId })

      // Clear state and navigate to course page
      clearState()
      navigate(`/courses/${String(currentState.courseId)}`)
    } catch (err) {
      console.error('Error finalizing quickstart:', err)
      setError(t().quickstart.errors.failedToFinalize)
      setIsLoading(false)
    }
  }

  // Handle professor update from regeneration
  const handleProfessorUpdate = (professor: QuickstartProfessorDetail) => {
    updateState({
      professor,
      professorId: professor.id,
    })
  }

  // Allow restarting the wizard
  const handleRestart = () => {
    clearState()
    setState({
      step: 'intent',
      query: '',
      courseId: null,
      professorId: null,
      departmentId: null,
      courseTitle: '',
      courseCode: '',
      professor: null,
    })
  }

  // Check for existing state on mount
  onMount(() => {
    const stored = getInitialState()
    if (stored.step !== 'intent' && stored.courseId) {
      // Resume from saved state
      setState(stored)
    }
  })

  return (
    <div class="min-h-screen py-12 px-4">
      <div class="max-w-4xl mx-auto">
        {/* Step Indicator */}
        <StepIndicator currentStep={currentStepNumber()} totalSteps={3} />

        {/* Error Display */}
        {error() && (
          <div class="arcane-card p-4 mb-6 border-danger bg-danger-bg/20 text-center">
            <p class="text-danger">{error()}</p>
            <button class="text-primary text-sm mt-2 hover:underline" onClick={handleRestart}>
              {t().quickstart.startOver}
            </button>
          </div>
        )}

        {/* Wizard Steps */}
        <Switch>
          <Match when={state().step === 'intent'}>
            <IntentStep
              onCourseGenerate={(query) => {
                void handleCourseGenerate(query)
              }}
              isLoading={isLoading()}
            />
          </Match>

          <Match when={state().step === 'professor' && state().professor}>
            <ProfessorStep
              professor={state().professor!}
              courseId={state().courseId!}
              courseTitle={state().courseTitle}
              departmentId={state().departmentId!}
              onAccept={() => {
                void handleProfessorAccept()
              }}
              onProfessorUpdate={handleProfessorUpdate}
              isLoading={isLoading()}
            />
          </Match>

          <Match when={state().step === 'complete'}>
            <div class="text-center">
              <h2 class="text-3xl font-display text-foreground mb-4">
                {t().quickstart.courseCreated}
              </h2>
              <p class="text-muted mb-6">{t().quickstart.courseBeingPrepared}</p>
            </div>
          </Match>
        </Switch>

        {/* Restart Link (only show after intent step) */}
        {state().step !== 'intent' && (
          <div class="text-center mt-8">
            <button
              class="text-muted text-sm hover:text-primary transition-colors"
              onClick={handleRestart}
            >
              {t().quickstart.startOver}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default Quickstart
