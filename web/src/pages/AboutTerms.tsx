import type { Component } from 'solid-js'
import { For, Show } from 'solid-js'
import { AboutSubpageLayout } from '../components/AboutSubpageLayout'
import { tos } from '../content/tos'

const AboutTerms: Component = () => (
  <AboutSubpageLayout title={tos.title}>
    <p class="text-xs text-muted mb-8 font-sans">Last Updated: {tos.lastUpdated}</p>

    <div class="space-y-2 text-muted leading-relaxed mb-10">
      <For each={tos.intro.split('\n\n')}>{(para) => <p>{para}</p>}</For>
    </div>

    <div class="space-y-10">
      <For each={tos.sections}>
        {(section) => (
          <div>
            <h2 class="font-display text-foreground text-xl mb-3">{section.heading}</h2>
            <div class="space-y-2 text-muted leading-relaxed">
              <For each={section.paragraphs}>{(para) => <p>{para}</p>}</For>
            </div>
            <Show when={section.items && section.items.length > 0}>
              <ul class="mt-3 space-y-1 list-disc list-inside text-muted">
                <For each={section.items}>{(item) => <li>{item}</li>}</For>
              </ul>
            </Show>
          </div>
        )}
      </For>
    </div>

    <Show when={tos.closing}>
      <p class="mt-10 pt-8 border-t border-border text-muted leading-relaxed italic">
        {tos.closing}
      </p>
    </Show>
  </AboutSubpageLayout>
)

export default AboutTerms
