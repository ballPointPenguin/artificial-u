import { A } from '@solidjs/router'
import type { Component } from 'solid-js'
import { useTranslations } from '../i18n'

const GITHUB_URL = 'https://github.com/ballPointPenguin/artificial-u'

export const Footer: Component = () => {
  const t = useTranslations()

  const linkClass = 'text-muted hover:text-primary transition-colors duration-200 text-sm'

  return (
    <footer class="bg-surface border-t border-border">
      {/* Main footer grid */}
      <div class="max-w-7xl mx-auto px-6 md:px-12 lg:px-16 py-12">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
          {/* Brand column */}
          <div class="sm:col-span-2 lg:col-span-1">
            <A href="/" class="flex items-center gap-3 no-underline mb-4">
              <div class="w-9 h-9 rounded-full border-2 border-secondary flex items-center justify-center">
                <span class="font-display text-sm text-secondary font-bold">A</span>
              </div>
              <span class="font-display text-sm tracking-[0.12em] uppercase text-foreground">
                {t().site.name}
              </span>
            </A>
            <p class="text-sm text-muted leading-relaxed max-w-xs">{t().footer.tagline}</p>
          </div>

          {/* Explore column */}
          <div>
            <h4 class="font-sans text-xs font-semibold uppercase tracking-widest text-foreground mb-4">
              {t().footer.explore}
            </h4>
            <nav class="flex flex-col gap-2.5">
              <A href="/courses" class={linkClass}>
                {t().footer.allCourses}
              </A>
              <A href="/departments" class={linkClass}>
                {t().footer.departments}
              </A>
              <A href="/professors" class={linkClass}>
                {t().footer.professors}
              </A>
              <A href="/search" class={linkClass}>
                {t().footer.search}
              </A>
            </nav>
          </div>

          {/* Create column */}
          <div>
            <h4 class="font-sans text-xs font-semibold uppercase tracking-widest text-foreground mb-4">
              {t().footer.create}
            </h4>
            <nav class="flex flex-col gap-2.5">
              <A href="/quickstart" class={linkClass}>
                {t().footer.getStarted}
              </A>
              <A href="/about/pricing" class={linkClass}>
                {t().footer.pricing}
              </A>
              <A href="/#how-it-works" class={linkClass}>
                {t().footer.howItWorks}
              </A>
              <A href="/about/faq" class={linkClass}>
                {t().footer.faq}
              </A>
            </nav>
          </div>

          {/* About column */}
          <div>
            <h4 class="font-sans text-xs font-semibold uppercase tracking-widest text-foreground mb-4">
              {t().footer.about}
            </h4>
            <nav class="flex flex-col gap-2.5">
              <A href="/about" class={linkClass}>
                {t().footer.aboutProject}
              </A>
              <A href="/about/ai-ethics" class={linkClass}>
                {t().footer.aiEthics}
              </A>
              <a href="mailto:bennie@aliencyb.org" class={linkClass}>
                {t().footer.contact}
              </a>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" class={linkClass}>
                {t().footer.github}
              </a>
            </nav>
          </div>
        </div>
      </div>

      {/* Bottom bar — pb-14 ensures legal links clear any fixed bottom overlays on mobile */}
      <div class="border-t border-border">
        <div class="max-w-7xl mx-auto px-6 md:px-12 lg:px-16 py-5 flex flex-col sm:flex-row justify-between items-center gap-3">
          <span class="text-xs text-muted">{t().footer.copyright}</span>
          <nav class="flex flex-wrap gap-x-6 gap-y-1">
            <A
              href="/about/privacy"
              class="text-xs text-muted hover:text-primary transition-colors"
            >
              {t().footer.privacyPolicy}
            </A>
            <A href="/about/terms" class="text-xs text-muted hover:text-primary transition-colors">
              {t().footer.termsOfService}
            </A>
            <A
              href="/about/ai-ethics"
              class="text-xs text-muted hover:text-primary transition-colors"
            >
              {t().footer.aiTransparency}
            </A>
          </nav>
        </div>
      </div>
    </footer>
  )
}
