import { A } from '@solidjs/router'
import type { Component } from 'solid-js'
import { useTranslations } from '../i18n'

const AboutPricing: Component = () => {
  const t = useTranslations()

  return (
    <div class="max-w-2xl mx-auto px-6 py-16 md:py-24">
      {/* Header */}
      <div class="text-center mb-16">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-full border border-primary/40 bg-surface mb-6">
          <span class="font-display text-2xl text-primary">¢</span>
        </div>
        <h1 class="text-3xl md:text-4xl font-display text-foreground mb-4">{t().pricing.title}</h1>
        <p class="text-lg text-muted leading-relaxed">{t().pricing.tagline}</p>
        <p class="text-sm text-muted leading-relaxed mt-3 max-w-md mx-auto">
          {t().pricing.taglineDetail}
        </p>
      </div>

      {/* Current status card */}
      <div class="border border-border bg-surface rounded-lg p-8 mb-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="inline-block w-2 h-2 rounded-full bg-primary" />
          <h2 class="font-sans text-xs font-semibold uppercase tracking-widest text-foreground">
            {t().pricing.currentStatus}
          </h2>
        </div>
        <p class="text-muted leading-relaxed mb-4">{t().pricing.currentStatusDetail}</p>
        <p class="text-muted leading-relaxed text-sm">{t().pricing.coinsExplained}</p>
      </div>

      {/* Want more card */}
      <div class="border border-primary/30 bg-primary/5 rounded-lg p-8 mb-12">
        <h2 class="font-display text-foreground text-lg mb-3">{t().pricing.wantMore}</h2>
        <p class="text-muted leading-relaxed mb-4">{t().pricing.wantMoreDetail}</p>
        <a
          href={`mailto:${t().pricing.contactCta}`}
          class="inline-block text-sm font-sans text-primary hover:underline tracking-wide"
        >
          {t().pricing.contactCta}
        </a>
      </div>

      {/* Footer note */}
      <div class="text-center">
        <p class="text-xs text-muted font-sans mb-6">{t().pricing.stayTuned}</p>
        <A
          href="/about"
          class="text-primary hover:underline text-sm font-sans uppercase tracking-wider"
        >
          &larr; About
        </A>
      </div>
    </div>
  )
}

export default AboutPricing
