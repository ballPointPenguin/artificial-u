import { FeatureCards } from '../components/FeaturedCards'
import { FeaturedFaculty } from '../components/FeaturedFaculty'
import { Hero } from '../components/ui/Hero'

const Home = () => {
  // Sample faculty data
  const facultyMembers = [
    {
      id: 'elowen-marsh',
      name: 'Professor Elowen Marsh',
      title: 'Chair of Quantum Humanities',
      shortName: 'Professor Elowen',
      imageUrl: '/images/faculty/elowen-marsh.png',
      specialty: 'Post-human Literature & AI Ethics',
    },
    {
      id: 'tobias-caldwell',
      name: 'Dr. Tobias Caldwell',
      title: 'Dean of Arcane Engineering',
      shortName: 'Dr. Tobias',
      imageUrl: '/images/faculty/tobias-caldwell.png',
      specialty: 'Hyper-dimensional Physics',
    },
    {
      id: 'morgana-thorne',
      name: 'Professor Morgana Thorne',
      title: 'Director of Esoteric Studies',
      shortName: 'Professor Morgana',
      imageUrl: '/images/faculty/morgana-thorne.png',
      specialty: 'Symbolic Systems & Neural Cryptography',
    },
  ]

  // Sample feature cards
  const featureCards = [
    {
      id: 'latest-news',
      title: 'Latest News',
      description: 'Read about our research and events',
      icon: 'book',
      link: '/news',
    },
    {
      id: 'philosophy',
      title: 'Our Philosophy',
      description: 'Pursue truth and wisdom',
      icon: 'column',
      link: '/about/philosophy',
    },
    {
      id: 'student-life',
      title: 'Student Life',
      description: 'Discover our campus and community',
      icon: 'hourglass',
      link: '/campus/student-life',
    },
  ]

  return (
    <div>
      {/* Hero Section */}
      <Hero
        title="Artificial University"
        subtitle="Expand Your Knowledge Beyond the Boundaries of Reality"
        buttonText="Learn More"
        buttonLink="#learn-more"
      />

      {/* Feature Cards */}
      <div id="learn-more">
        <FeatureCards features={featureCards} />
      </div>

      {/* About Section */}
      <section class="py-20 bg-arcanum-900 relative overflow-hidden">
        {/* Background effect */}
        <div class="absolute inset-0 opacity-20" aria-hidden="true">
          <div class="absolute top-0 right-0 w-1/2 h-full bg-vaporwave-800/10 rounded-full filter blur-3xl" />
        </div>

        <div class="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="text-center mb-12">
            <h2 class="text-3xl md:text-4xl font-display text-parchment-200 mb-6 text-shadow-golden">
              Where Ancient Wisdom Meets Future Innovation
            </h2>
            <div class="w-20 h-1 bg-gradient-to-r from-parchment-800 to-mystic-800 mx-auto" />
          </div>

          <div class="prose prose-lg prose-invert mx-auto font-serif text-parchment-300">
            <p class="text-lg md:text-xl leading-relaxed">
              Founded in 2025, The Artificial University exists at the intersection of timeless
              esoteric traditions and cutting-edge scientific discovery. Our unique curriculum
              bridges quantum mechanics, symbolic systems, and the digital humanities to foster a
              new generation of scholars capable of navigating the increasingly complex fabric of
              reality.
            </p>
            <p class="text-lg md:text-xl leading-relaxed">
              Through rigorous intellectual training and immersive learning environments, our
              students develop the cognitive flexibility to harmonize seemingly contradictory
              domains of knowledge, cultivating a holistic understanding that transcends
              conventional academic boundaries.
            </p>
          </div>

          <div class="mt-12 text-center">
            <a
              href="/about"
              class="inline-block px-6 py-3 border border-parchment-400 text-parchment-200 bg-arcanum-800/50 hover:bg-arcanum-700/50 transition-colors duration-300 rounded font-serif tracking-wider"
            >
              Discover Our Story
            </a>
          </div>
        </div>
      </section>

      {/* Featured Faculty */}
      <FeaturedFaculty title="Distinguished Faculty" faculty={facultyMembers} />
      {/* CTA Section */}
      <section class="py-20 bg-gradient-to-b from-arcanum-900 to-arcanum-950 relative overflow-hidden">
        <div class="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 class="text-3xl md:text-4xl font-display text-parchment-100 mb-6 text-shadow-golden">
            Begin Your Journey Into The Unknown
          </h2>
          <p class="text-xl font-serif text-parchment-300 mb-10 max-w-2xl mx-auto">
            Applications are now open for the 2025 academic year. Join our community of seekers,
            thinkers, and creators.
          </p>
          <a
            href="/admissions/apply"
            class="inline-block px-8 py-4 bg-gradient-to-r from-parchment-700/50 to-mystic-800/50 text-parchment-100 font-display text-lg tracking-wider border border-parchment-500/50 rounded shadow-arcane hover:shadow-glow transition-all duration-300"
          >
            Apply Now
          </a>
        </div>
      </section>
    </div>
  )
}

export default Home
