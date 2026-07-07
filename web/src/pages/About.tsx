import type { Component } from 'solid-js'
import { useTranslations } from '../i18n'

const About: Component = () => {
  const t = useTranslations()
  return (
    <div class="min-h-screen bg-arcanum-900">
      {/* Page Header */}
      <section class="py-16 bg-gradient-to-b from-arcanum-800 to-arcanum-900 border-b border-parchment-800/30">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 class="text-4xl md:text-5xl font-display text-parchment-100 mb-4 text-shadow-golden">
            {t().about.title}
          </h1>
          <p class="text-xl font-serif text-parchment-300">{t().about.subtitle}</p>
        </div>
      </section>

      {/* Main Content */}
      <section class="py-16">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="prose prose-lg prose-invert font-serif text-parchment-300 space-y-8">
            {/* Important Notice */}
            <div class="bg-red-900/20 border-2 border-red-500/50 rounded-lg p-6 mb-8">
              <h2 class="text-2xl font-display text-red-300 mb-4">
                {t().about.importantNotice.title}
              </h2>
              <div class="space-y-3 text-parchment-200">
                <p class="leading-relaxed font-semibold">
                  {t().about.importantNotice.notAccredited}
                </p>
                <p class="leading-relaxed">{t().about.importantNotice.experimental}</p>
                <p class="leading-relaxed">{t().about.importantNotice.alphaStage}</p>
              </div>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">
                {t().about.whatThisIs.title}
              </h2>
              <p class="leading-relaxed">{t().about.whatThisIs.content}</p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">
                {t().about.howItWorks.title}
              </h2>
              <p class="leading-relaxed">{t().about.howItWorks.intro}</p>
              <p class="leading-relaxed mt-4">{t().about.howItWorks.outro}</p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">
                {t().about.whatThisIsNot.title}
              </h2>
              <p class="leading-relaxed">{t().about.whatThisIsNot.content}</p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">
                {t().about.alphaStatus.title}
              </h2>
              <p class="leading-relaxed">{t().about.alphaStatus.content}</p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">
                {t().about.openSource.title}
              </h2>
              <p class="leading-relaxed">{t().about.openSource.content}</p>
              <div class="mt-4">
                <a
                  href="https://github.com/ballPointPenguin/artificial-u"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-2 text-parchment-200 hover:text-parchment-100 underline decoration-parchment-400 hover:decoration-parchment-200 transition-colors duration-200"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      fill-rule="evenodd"
                      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  {t().about.openSource.viewOnGitHub}
                </a>
              </div>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">
                {t().about.creator.title}
              </h2>
              <p class="leading-relaxed">
                {t().about.creator.bio}{' '}
                <a
                  href="mailto:ben@aliencyb.org"
                  class="text-parchment-200 hover:text-parchment-100 underline decoration-parchment-400 hover:decoration-parchment-200 transition-colors duration-200"
                >
                  ben@aliencyb.org
                </a>
                .
              </p>
              <p class="leading-relaxed mt-4">{t().about.creator.outro}</p>
            </div>
          </div>

          <div class="mt-12 text-center">
            <a
              href="/browse"
              class="inline-block px-6 py-3 border border-parchment-400 text-parchment-200 bg-arcanum-800/50 hover:bg-arcanum-700/50 transition-colors duration-300 rounded font-serif tracking-wider"
            >
              {t().about.exploreCourses}
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}

export default About
