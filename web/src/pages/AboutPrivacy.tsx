import type { Component } from 'solid-js'
import { For, Show } from 'solid-js'
import { AboutSubpageLayout } from '../components/AboutSubpageLayout'
import { privacy } from '../content/privacy'

const AboutPrivacy: Component = () => (
  <AboutSubpageLayout title={privacy.title}>
    <p class="text-xs text-muted mb-8 font-sans">Last Updated: {privacy.lastUpdated}</p>

    <div class="space-y-2 text-muted leading-relaxed mb-10">
      <For each={privacy.intro.split('\n\n')}>{(para) => <p>{para}</p>}</For>
    </div>

    <div class="space-y-10">
      <For each={privacy.sections}>
        {(section) => (
          <div>
            <h2 class="font-display text-foreground text-xl mb-3">{section.heading}</h2>

            <Show when={section.paragraphs && section.paragraphs.length > 0}>
              <div class="space-y-2 text-muted leading-relaxed">
                <For each={section.paragraphs}>{(para) => <p>{para}</p>}</For>
              </div>
            </Show>

            <Show when={section.items && section.items.length > 0}>
              <ul class="mt-3 space-y-1 list-disc list-inside text-muted">
                <For each={section.items}>{(item) => <li>{item}</li>}</For>
              </ul>
            </Show>

            <Show when={section.subsections && section.subsections.length > 0}>
              <div class="mt-4 space-y-6 pl-4 border-l border-border">
                <For each={section.subsections}>
                  {(sub) => (
                    <div>
                      <Show when={sub.subheading}>
                        <h3 class="font-sans text-sm font-semibold uppercase tracking-widest text-foreground mb-2">
                          {sub.subheading}
                        </h3>
                      </Show>
                      <Show when={sub.paragraphs}>
                        <div class="space-y-2 text-muted leading-relaxed">
                          <For each={sub.paragraphs}>{(para) => <p>{para}</p>}</For>
                        </div>
                      </Show>
                      <Show when={sub.items && sub.items.length > 0}>
                        <ul class="mt-3 space-y-1 list-disc list-inside text-muted">
                          <For each={sub.items}>{(item) => <li>{item}</li>}</For>
                        </ul>
                      </Show>
                    </div>
                  )}
                </For>
              </div>
            </Show>
          </div>
        )}
      </For>
    </div>

    <Show when={privacy.closing}>
      <p class="mt-10 pt-8 border-t border-border text-muted leading-relaxed italic">
        {privacy.closing}
      </p>
    </Show>
  </AboutSubpageLayout>
)

export default AboutPrivacy
