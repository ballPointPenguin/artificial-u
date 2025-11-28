import type { Component } from 'solid-js'
import { createSignal, Show } from 'solid-js'
import { quickstartService } from '../../api/services/quickstart-service.js'
import type { QuickstartProfessorDetail } from '../../api/types.js'
import { useI18n } from '../../i18n/index.js'
import { Button } from '../ui'

interface ProfessorStepProps {
  professor: QuickstartProfessorDetail
  courseId: number
  courseTitle: string
  departmentId: number
  onAccept: () => void
  onProfessorUpdate: (professor: QuickstartProfessorDetail) => void
  isLoading: boolean
}

type ChangeOption = 'image' | 'voice' | 'details' | null

export const ProfessorStep: Component<ProfessorStepProps> = (props) => {
  const { t } = useI18n()
  const [changeOption, setChangeOption] = createSignal<ChangeOption>(null)
  const [freeformPrompt, setFreeformPrompt] = createSignal('')
  const [isRegenerating, setIsRegenerating] = createSignal(false)
  const [introAudioUrl, setIntroAudioUrl] = createSignal<string | null>(null)
  const [isGeneratingAudio, setIsGeneratingAudio] = createSignal(false)
  const [error, setError] = createSignal('')

  const generateIntroAudio = async () => {
    setIsGeneratingAudio(true)
    setError('')
    try {
      const result = await quickstartService.generateIntroAudio({
        professor_id: props.professor.id,
        course_title: props.courseTitle,
      })
      setIntroAudioUrl(result.audio_data_uri)
    } catch (err) {
      console.error('Error generating intro audio:', err)
      setError(t().quickstart.errors.failedToGenerateVoice)
    } finally {
      setIsGeneratingAudio(false)
    }
  }

  const handleRegenerateImage = async () => {
    setIsRegenerating(true)
    setError('')
    try {
      const result = await quickstartService.regenerateProfessorImage({
        professor_id: props.professor.id,
        course_id: props.courseId,
      })
      props.onProfessorUpdate(result.professor)
      setChangeOption(null)
    } catch (err) {
      console.error('Error regenerating image:', err)
      setError(t().quickstart.errors.failedToRegenerateImage)
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleReassignVoice = async () => {
    setIsRegenerating(true)
    setError('')
    try {
      const result = await quickstartService.reassignProfessorVoice({
        professor_id: props.professor.id,
        course_id: props.courseId,
      })
      props.onProfessorUpdate(result.professor)
      setIntroAudioUrl(null) // Clear cached audio
      setChangeOption(null)
    } catch (err) {
      console.error('Error reassigning voice:', err)
      setError(t().quickstart.errors.failedToReassignVoice)
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleRegenerateProfessor = async () => {
    setIsRegenerating(true)
    setError('')
    try {
      const result = await quickstartService.regenerateProfessor({
        course_id: props.courseId,
        department_id: props.departmentId,
        freeform_prompt: freeformPrompt() || undefined,
      })
      props.onProfessorUpdate(result.professor)
      setIntroAudioUrl(null) // Clear cached audio
      setFreeformPrompt('')
      setChangeOption(null)
    } catch (err) {
      console.error('Error regenerating professor:', err)
      setError(t().quickstart.errors.failedToRegenerateProfessor)
    } finally {
      setIsRegenerating(false)
    }
  }

  return (
    <div class="max-w-2xl mx-auto">
      <div class="text-center mb-8">
        <h2 class="text-3xl font-display text-foreground mb-2">{t().quickstart.professor.title}</h2>
        <p class="text-muted font-serif">
          {t().quickstart.professor.guideThroughCourse}{' '}
          <span class="text-primary">{props.courseTitle}</span>
        </p>
      </div>

      {/* Professor Card */}
      <div class="arcane-card p-6 mb-6">
        <div class="flex flex-col md:flex-row gap-6">
          {/* Professor Image */}
          <div class="flex-shrink-0">
            <div class="w-32 h-32 md:w-40 md:h-40 rounded-full overflow-hidden border-4 border-accent/30 shadow-arcane mx-auto md:mx-0">
              <Show
                when={props.professor.image_url}
                fallback={
                  <div class="w-full h-full bg-surface flex items-center justify-center">
                    <span class="text-4xl text-muted">?</span>
                  </div>
                }
              >
                <img
                  src={props.professor.image_url!}
                  alt={props.professor.name}
                  class="w-full h-full object-cover"
                />
              </Show>
            </div>
          </div>

          {/* Professor Details */}
          <div class="flex-1 text-center md:text-left">
            <h3 class="text-2xl font-display text-foreground">{props.professor.name}</h3>
            <p class="text-primary font-serif">{props.professor.title}</p>
            <p class="text-sm text-muted mb-3">{props.professor.specialization}</p>

            <Show when={props.professor.description}>
              <p class="text-foreground/80 text-sm mb-3">{props.professor.description}</p>
            </Show>

            <Show when={props.professor.teaching_style}>
              <p class="text-xs text-muted italic">
                <span class="font-semibold">{t().quickstart.professor.teachingStyle}</span>{' '}
                {props.professor.teaching_style}
              </p>
            </Show>
          </div>
        </div>

        {/* Voice Preview */}
        <div class="mt-6 pt-4 border-t border-border">
          <div class="flex items-center justify-center gap-4">
            <Show
              when={introAudioUrl()}
              fallback={
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    void generateIntroAudio()
                  }}
                  disabled={isGeneratingAudio() || !props.professor.voice_id}
                >
                  {isGeneratingAudio() ? (
                    <span class="flex items-center gap-2">
                      <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle
                          class="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          stroke-width="4"
                          fill="none"
                        />
                        <path
                          class="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      {t().quickstart.professor.generating}
                    </span>
                  ) : (
                    t().quickstart.professor.hearTheirVoice
                  )}
                </Button>
              }
            >
              <audio controls src={introAudioUrl()!} class="max-w-xs" />
            </Show>

            <Show when={props.professor.voice_preview_url && !introAudioUrl()}>
              <span class="text-xs text-muted">{t().quickstart.professor.or}</span>
              <a
                href={props.professor.voice_preview_url!}
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary text-sm hover:underline"
              >
                {t().quickstart.professor.sampleVoice}
              </a>
            </Show>
          </div>
        </div>
      </div>

      {/* Error Message */}
      <Show when={error()}>
        <div class="text-danger text-sm text-center mb-4">{error()}</div>
      </Show>

      {/* Change Options */}
      <Show when={changeOption()}>
        <div class="arcane-card p-4 mb-6">
          <Show when={changeOption() === 'image'}>
            <div class="text-center">
              <p class="text-muted mb-4">
                {t().quickstart.professor.generateNewPortrait} {props.professor.name}?
              </p>
              <div class="flex justify-center gap-3">
                <Button variant="secondary" size="sm" onClick={() => setChangeOption(null)}>
                  {t().common.cancel}
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    void handleRegenerateImage()
                  }}
                  disabled={isRegenerating()}
                >
                  {isRegenerating()
                    ? t().quickstart.professor.regenerating
                    : t().quickstart.professor.regenerateImage}
                </Button>
              </div>
            </div>
          </Show>

          <Show when={changeOption() === 'voice'}>
            <div class="text-center">
              <p class="text-muted mb-4">
                {t().quickstart.professor.assignDifferentVoice} {props.professor.name}?
              </p>
              <div class="flex justify-center gap-3">
                <Button variant="secondary" size="sm" onClick={() => setChangeOption(null)}>
                  {t().common.cancel}
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    void handleReassignVoice()
                  }}
                  disabled={isRegenerating()}
                >
                  {isRegenerating()
                    ? t().quickstart.professor.assigning
                    : t().quickstart.professor.reassignVoice}
                </Button>
              </div>
            </div>
          </Show>

          <Show when={changeOption() === 'details'}>
            <div>
              <p class="text-muted mb-3 text-center">
                {t().quickstart.professor.describeProfessorPreference}
              </p>
              <textarea
                value={freeformPrompt()}
                onInput={(e) => setFreeformPrompt(e.currentTarget.value)}
                placeholder={t().quickstart.professor.professorPromptPlaceholder}
                class="arcane-input w-full min-h-24 resize-y mb-4"
              />
              <div class="flex justify-center gap-3">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setChangeOption(null)
                    setFreeformPrompt('')
                  }}
                >
                  {t().common.cancel}
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    void handleRegenerateProfessor()
                  }}
                  disabled={isRegenerating()}
                >
                  {isRegenerating()
                    ? t().quickstart.professor.generating
                    : t().quickstart.professor.generateNewProfessor}
                </Button>
              </div>
            </div>
          </Show>
        </div>
      </Show>

      {/* Action Buttons */}
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <Button
          variant="primary"
          size="lg"
          onClick={props.onAccept}
          disabled={props.isLoading || isRegenerating()}
          class="min-w-48"
        >
          {props.isLoading
            ? t().quickstart.professor.creatingCourse
            : t().quickstart.professor.useThisTeacher}
        </Button>

        <Show when={!changeOption()}>
          <div class="relative">
            <Button
              variant="secondary"
              size="lg"
              onClick={() => setChangeOption('details')}
              disabled={isRegenerating()}
            >
              {t().quickstart.professor.regenerate}
            </Button>
          </div>

          <div class="relative group">
            <Button variant="outline" size="lg" disabled={isRegenerating()}>
              {t().quickstart.professor.changeSomething}
            </Button>
            <div class="absolute top-full left-1/2 -translate-x-1/2 mt-2 hidden group-hover:block z-10">
              <div class="arcane-card p-2 shadow-lg min-w-32">
                <button
                  class="w-full text-left px-3 py-2 text-sm hover:bg-primary/10 rounded transition-colors"
                  onClick={() => setChangeOption('image')}
                >
                  {t().quickstart.professor.image}
                </button>
                <button
                  class="w-full text-left px-3 py-2 text-sm hover:bg-primary/10 rounded transition-colors"
                  onClick={() => setChangeOption('voice')}
                >
                  {t().quickstart.professor.voice}
                </button>
                <button
                  class="w-full text-left px-3 py-2 text-sm hover:bg-primary/10 rounded transition-colors"
                  onClick={() => setChangeOption('details')}
                >
                  {t().quickstart.professor.details}
                </button>
              </div>
            </div>
          </div>
        </Show>
      </div>
    </div>
  )
}
