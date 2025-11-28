import type { Component } from 'solid-js'
import { For } from 'solid-js'
import { useI18n } from '../../i18n/index.js'

interface StepIndicatorProps {
  currentStep: number
  totalSteps: number
  stepLabels?: string[]
}

export const StepIndicator: Component<StepIndicatorProps> = (props) => {
  const { t } = useI18n()

  const defaultLabels = () => [
    t().quickstart.steps.intent,
    t().quickstart.steps.professor,
    t().quickstart.steps.complete,
  ]

  const labels = () => props.stepLabels || defaultLabels()

  return (
    <div class="flex items-center justify-center gap-2 mb-8">
      <For each={labels()}>
        {(label, index) => (
          <>
            <div class="flex flex-col items-center">
              <div
                class={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-serif border-2 transition-all duration-300 ${
                  index() + 1 < props.currentStep
                    ? 'bg-primary text-on-primary border-primary'
                    : index() + 1 === props.currentStep
                      ? 'bg-primary/20 text-primary border-primary shadow-glow'
                      : 'bg-surface text-muted border-border'
                }`}
              >
                {index() + 1 < props.currentStep ? (
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fill-rule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                ) : (
                  index() + 1
                )}
              </div>
              <span
                class={`text-xs mt-1 font-serif ${
                  index() + 1 <= props.currentStep ? 'text-primary' : 'text-muted'
                }`}
              >
                {label}
              </span>
            </div>
            {index() < labels().length - 1 && (
              <div
                class={`w-12 h-0.5 mb-5 transition-all duration-300 ${
                  index() + 1 < props.currentStep ? 'bg-primary' : 'bg-border'
                }`}
              />
            )}
          </>
        )}
      </For>
    </div>
  )
}
