import type { Component } from 'solid-js'

const About: Component = () => {
  return (
    <div class="min-h-screen bg-arcanum-900">
      {/* Page Header */}
      <section class="py-16 bg-gradient-to-b from-arcanum-800 to-arcanum-900 border-b border-parchment-800/30">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 class="text-4xl md:text-5xl font-display text-parchment-100 mb-4 text-shadow-golden">
            About Artificial University
          </h1>
          <p class="text-xl font-serif text-parchment-300">Our mission and approach to education</p>
        </div>
      </section>

      {/* Main Content */}
      <section class="py-16">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="prose prose-lg prose-invert font-serif text-parchment-300 space-y-8">
            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">Who We Are</h2>
              <p class="leading-relaxed">
                The Artificial University is an experimental platform for learning where artificial
                intelligence and human expertise combine to create educational content. We generate
                courses across diverse fields of study, making knowledge accessible to anyone with
                curiosity.
              </p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">Our Approach</h2>
              <p class="leading-relaxed">
                Rather than replacing traditional education, we explore a new model: leveraging AI
                to rapidly generate course materials while maintaining academic rigor and human
                judgment. Our faculty curates and shapes the generated content, ensuring quality and
                relevance.
              </p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">What You'll Find Here</h2>
              <p class="leading-relaxed">
                Browse our growing catalog of courses covering science, humanities, technology, and
                more. Each course includes lecture materials, structured topics, and summaries
                designed to support your learning journey.
              </p>
            </div>
          </div>

          <div class="mt-12 text-center">
            <a
              href="/courses"
              class="inline-block px-6 py-3 border border-parchment-400 text-parchment-200 bg-arcanum-800/50 hover:bg-arcanum-700/50 transition-colors duration-300 rounded font-serif tracking-wider"
            >
              Explore Courses
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}

export default About
