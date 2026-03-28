import { A } from '@solidjs/router'
import type { Component, JSX } from 'solid-js'

export type AboutSubpageLayoutProps = {
  title: string
  children?: JSX.Element
}

export const AboutSubpageLayout: Component<AboutSubpageLayoutProps> = (props) => (
  <div class="max-w-3xl mx-auto px-6 py-16 md:py-20">
    <h1 class="text-3xl md:text-4xl font-display text-foreground mb-4">{props.title}</h1>
    <div class="w-16 h-px bg-primary mb-8" />
    {props.children}
    <p class="mt-12">
      <A
        href="/about"
        class="text-primary hover:underline text-sm font-sans uppercase tracking-wider"
      >
        &larr; About
      </A>
    </p>
  </div>
)
