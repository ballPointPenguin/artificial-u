import { useNavigate } from '@solidjs/router'
import type { Component } from 'solid-js'
import { createSignal, For, Show } from 'solid-js'
import { quickstartService } from '../../api/services/quickstart-service.js'
import type { QuickstartCourseBrief, QuickstartMatchResponse } from '../../api/types.js'
import { useI18n } from '../../i18n/index.js'
import { Button } from '../ui'

interface IntentStepProps {
  onCourseGenerate: (query: string) => void
  isLoading: boolean
}

export const IntentStep: Component<IntentStepProps> = (props) => {
  const { t } = useI18n()
  const navigate = useNavigate()
  const [query, setQuery] = createSignal('')
  const [matchResult, setMatchResult] = createSignal<QuickstartMatchResponse | null>(null)
  const [isMatching, setIsMatching] = createSignal(false)
  const [error, setError] = createSignal('')

  const handleSubmit = async (e: Event) => {
    e.preventDefault()
    const q = query().trim()
    if (!q) return

    setError('')
    setIsMatching(true)

    try {
      const result = await quickstartService.matchCourses({ query: q })
      setMatchResult(result)

      // If no matches or GENERATE action, proceed directly
      if (result.action === 'GENERATE' || result.matched_courses.length === 0) {
        props.onCourseGenerate(q)
      }
    } catch (err) {
      console.error('Error matching courses:', err)
      setError(t().quickstart.errors.failedToSearch)
    } finally {
      setIsMatching(false)
    }
  }

  const handleListenNow = (course: QuickstartCourseBrief) => {
    navigate(`/courses/${String(course.id)}`)
  }

  const handleBuildNew = () => {
    props.onCourseGenerate(query())
  }

  const isSubmitDisabled = () => query().trim().length < 3 || isMatching() || props.isLoading

  return (
    <div class="max-w-2xl mx-auto">
      <Show
        when={!matchResult() || matchResult()?.action === 'GENERATE'}
        fallback={
          // Show matched courses
          <div class="space-y-6">
            <div class="text-center">
              <h2 class="text-2xl font-display text-foreground mb-2">
                {t().quickstart.intent.coursesFound}
              </h2>
              <p class="text-muted font-serif">{matchResult()?.reasoning}</p>
            </div>

            <div class="space-y-4">
              <For each={matchResult()?.matched_courses}>
                {(course) => (
                  <div class="arcane-card p-4 flex gap-4 items-start">
                    <Show when={course.professor_image_url}>
                      <img
                        src={course.professor_image_url!}
                        alt={course.professor_name || t().quickstart.steps.professor}
                        class="w-16 h-16 rounded-full object-cover border-2 border-accent/30"
                      />
                    </Show>
                    <div class="flex-1">
                      <h3 class="font-display text-lg text-foreground">{course.title}</h3>
                      <p class="text-sm text-muted font-serif mb-2">
                        {course.code}
                        {course.professor_name && ` • ${course.professor_name}`}
                      </p>
                      <p class="text-sm text-foreground/80 line-clamp-2">{course.description}</p>
                    </div>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        handleListenNow(course)
                      }}
                    >
                      {t().quickstart.intent.listenNow}
                    </Button>
                  </div>
                )}
              </For>
            </div>

            <div class="text-center pt-4 border-t border-border">
              <p class="text-muted text-sm mb-3">{t().quickstart.intent.wantSomethingDifferent}</p>
              <Button variant="secondary" onClick={handleBuildNew} disabled={props.isLoading}>
                {props.isLoading
                  ? t().quickstart.intent.creating
                  : t().quickstart.intent.buildSomethingNew}
              </Button>
            </div>
          </div>
        }
      >
        {/* Initial query form */}
        <div class="text-center mb-8">
          <h1 class="text-4xl font-display text-foreground mb-4 text-shadow-golden">
            {t().quickstart.intent.title}
          </h1>
          <p class="text-muted font-serif text-lg">{t().quickstart.intent.subtitle}</p>
        </div>

        <form
          onSubmit={(e) => {
            void handleSubmit(e)
          }}
          class="space-y-6"
        >
          <div>
            <textarea
              value={query()}
              onInput={(e) => setQuery(e.currentTarget.value)}
              placeholder={t().quickstart.intent.placeholder}
              class="arcane-input w-full min-h-32 resize-y"
              disabled={isMatching() || props.isLoading}
            />
            <p class="text-xs text-muted mt-2">{t().quickstart.intent.hint}</p>
          </div>

          <Show when={error()}>
            <div class="text-danger text-sm">{error()}</div>
          </Show>

          <div class="flex justify-center">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={isSubmitDisabled()}
              class="min-w-48"
            >
              {isMatching() ? (
                <span class="flex items-center gap-2">
                  <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
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
                  {t().quickstart.intent.searching}
                </span>
              ) : props.isLoading ? (
                <span class="flex items-center gap-2">
                  <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
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
                  {t().quickstart.intent.creatingCourse}
                </span>
              ) : (
                t().quickstart.intent.startLearning
              )}
            </Button>
          </div>
        </form>
      </Show>
    </div>
  )
}
