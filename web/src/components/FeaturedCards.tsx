import { A } from '@solidjs/router'
import { For } from 'solid-js'

interface FeatureCard {
  id: string
  title: string
  description: string
  icon: string // SVG path or icon component name
  link: string
}

interface FeatureCardsProps {
  features: FeatureCard[]
}

// SVG Icons
const icons = {
  book: (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-10 h-10"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  ),
  column: (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-10 h-10"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <circle cx="12" cy="8" r="7" />
      <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88" />
    </svg>
  ),
  hourglass: (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-10 h-10"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M5 22h14" />
      <path d="M5 2h14" />
      <path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22" />
      <path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2" />
    </svg>
  ),
}

export function FeatureCards(props: FeatureCardsProps) {
  return (
    <section class="bg-arcanum-950 py-16 relative">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <For each={props.features}>
            {(feature) => (
              <A
                href={feature.link}
                class="group block bg-arcanum-900 border border-parchment-800/30 rounded-sm p-6 transition-all duration-300 hover:bg-arcanum-800 hover:shadow-arcane"
              >
                <div class="flex flex-col items-center text-center space-y-4">
                  <div class="text-parchment-300 group-hover:text-parchment-200 transition-colors">
                    {icons[feature.icon as keyof typeof icons]}
                  </div>

                  <h3 class="text-parchment-200 font-display text-xl tracking-wide">
                    {feature.title}
                  </h3>

                  <p class="text-parchment-400 font-serif group-hover:text-parchment-300 transition-colors">
                    {feature.description}
                  </p>
                </div>
              </A>
            )}
          </For>
        </div>
      </div>
    </section>
  )
}
