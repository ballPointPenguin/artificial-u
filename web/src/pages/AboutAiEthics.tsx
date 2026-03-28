import type { Component } from 'solid-js'
import { For, Show } from 'solid-js'
import { AboutSubpageLayout } from '../components/AboutSubpageLayout'
import { ethics } from '../content/ethics'

const AboutAiEthics: Component = () => (
  <AboutSubpageLayout title={ethics.title}>
    <div class="space-y-10">
      <For each={ethics.sections}>
        {(section) => (
          <div>
            <h2 class="font-display text-foreground text-xl mb-3">{section.heading}</h2>
            <div class="space-y-3 text-muted leading-relaxed">
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
  </AboutSubpageLayout>
)

export default AboutAiEthics
