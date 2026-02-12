import { A } from '@solidjs/router'
import type { Component } from 'solid-js'

const PAGE_TITLES: Record<string, string> = {
  '/about/privacy': 'Privacy Policy',
  '/about/terms': 'Terms of Service',
  '/about/ai-ethics': 'AI Usage & Ethics',
  '/about/pricing': 'Pricing',
  '/about/faq': 'Frequently Asked Questions',
}

const ComingSoon: Component = () => {
  const path = typeof window !== 'undefined' ? window.location.pathname : ''
  const title = PAGE_TITLES[path] ?? 'Coming Soon'

  return (
    <div class="max-w-3xl mx-auto px-6 py-20 text-center">
      <h1 class="text-3xl md:text-4xl font-display text-foreground mb-4">{title}</h1>
      <div class="w-16 h-px bg-primary mx-auto mb-6" />
      <p class="text-muted text-lg leading-relaxed mb-8">
        This page is coming soon. We're working on thoughtful, transparent content for this section.
      </p>
      <A href="/" class="text-primary hover:underline text-sm font-sans uppercase tracking-wider">
        &larr; Back to Home
      </A>
    </div>
  )
}

export default ComingSoon
