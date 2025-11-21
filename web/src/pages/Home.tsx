import { Hero } from '../components/ui'
import { useTranslations } from '../i18n'

const Home = () => {
  const t = useTranslations()
  return (
    <div>
      {/* Hero Section */}
      <Hero
        title={t().home.hero.title}
        subtitle={t().home.hero.subtitle}
        buttonText={t().home.hero.buttonText}
        buttonLink="#home-content"
      />

      {/* Disclaimer Notice */}
      <section id="home-content" class="py-8 bg-arcanum-900">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="border-2 border-red-500 bg-red-900/20 rounded-lg p-6">
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0 text-red-400 text-2xl font-bold">⚠</div>
              <div class="flex-1">
                <h2 class="text-xl font-display text-red-300 mb-3 font-bold">
                  {t().home.disclaimer.title}
                </h2>
                <div class="space-y-2 font-serif text-parchment-200">
                  <p class="font-semibold">{t().home.disclaimer.alphaNotice}</p>
                  <p>{t().home.disclaimer.notAccredited}</p>
                  <p>
                    {t().home.disclaimer.noFormalEducation}{' '}
                    <a href="/about" class="text-red-300 hover:text-red-200 underline">
                      {t().home.disclaimer.aboutLink}
                    </a>{' '}
                    {t().home.disclaimer.forFullDetails}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Welcome Section */}
      <section class="py-20 bg-arcanum-900 relative overflow-hidden">
        {/* Background effect */}
        <div class="absolute inset-0 opacity-20" aria-hidden="true">
          <div class="absolute top-0 right-0 w-1/2 h-full bg-vaporwave-800/10 rounded-full filter blur-3xl" />
        </div>

        <div class="relative z-10 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="prose prose-lg prose-invert mx-auto font-serif text-parchment-300">
            <p class="text-lg md:text-xl leading-relaxed">{t().home.welcome.intro}</p>
            <p class="text-lg md:text-xl leading-relaxed">{t().home.welcome.explore}</p>
          </div>

          <div class="mt-12 text-center">
            <a
              href="/courses"
              class="inline-block px-6 py-3 border border-parchment-400 text-parchment-200 bg-arcanum-800/50 hover:bg-arcanum-700/50 transition-colors duration-300 rounded font-serif tracking-wider"
            >
              {t().home.welcome.viewAllCourses}
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home
