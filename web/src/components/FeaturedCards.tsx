import { A } from '@solidjs/router'
import { For, type Component, type JSX } from 'solid-js'

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
const icons: Record<string, JSX.Element> = {
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

const FeatureCardItem: Component<{ feature: FeatureCard }> = (props) => {
  const { feature } = props
  return (
    <A
      href={feature.link}
      class="group block bg-surface border border-border/30 rounded-sm p-6 transition-all duration-300 hover:bg-surface/70 hover:shadow-arcane"
    >
      <div class="flex flex-col items-center text-center space-y-4">
        <div class="text-accent group-hover:text-primary transition-colors">
          {icons[feature.icon as keyof typeof icons]}
        </div>
        <h3 class="text-foreground font-display text-xl tracking-wide group-hover:text-primary transition-colors">
          {feature.title}
        </h3>
        <p class="text-muted font-serif group-hover:text-muted/80 transition-colors">
          {feature.description}
        </p>
      </div>
    </A>
  )
}

export function FeatureCards(props: FeatureCardsProps) {
  return (
    <section class="bg-background py-16 relative">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <For each={props.features}>{(feature) => <FeatureCardItem feature={feature} />}</For>
        </div>
      </div>
    </section>
  )
}
