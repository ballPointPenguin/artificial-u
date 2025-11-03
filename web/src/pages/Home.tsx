import { Hero } from '../components/ui'

const Home = () => {
  return (
    <div>
      {/* Hero Section */}
      <Hero
        title="Artificial University"
        subtitle="Explore knowledge crafted by AI, shaped by your curiosity"
        buttonText="Browse Courses"
        buttonLink="/courses"
      />

      {/* Welcome Section */}
      <section class="py-20 bg-arcanum-900 relative overflow-hidden">
        {/* Background effect */}
        <div class="absolute inset-0 opacity-20" aria-hidden="true">
          <div class="absolute top-0 right-0 w-1/2 h-full bg-vaporwave-800/10 rounded-full filter blur-3xl" />
        </div>

        <div class="relative z-10 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="prose prose-lg prose-invert mx-auto font-serif text-parchment-300">
            <p class="text-lg md:text-xl leading-relaxed">
              Welcome to the Artificial University. Here you'll find a growing collection of courses
              generated through a collaboration between artificial intelligence and human expertise.
              Each course is designed to make complex subjects accessible and engaging.
            </p>
            <p class="text-lg md:text-xl leading-relaxed">
              Explore our curriculum, learn from our faculty, and discover new fields of study.
            </p>
          </div>

          <div class="mt-12 text-center">
            <a
              href="/courses"
              class="inline-block px-6 py-3 border border-parchment-400 text-parchment-200 bg-arcanum-800/50 hover:bg-arcanum-700/50 transition-colors duration-300 rounded font-serif tracking-wider"
            >
              View All Courses
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home
