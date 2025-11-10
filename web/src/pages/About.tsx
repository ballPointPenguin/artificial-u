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
          <p class="text-xl font-serif text-parchment-300">An experimental AI content platform</p>
        </div>
      </section>

      {/* Main Content */}
      <section class="py-16">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="prose prose-lg prose-invert font-serif text-parchment-300 space-y-8">
            {/* Important Notice */}
            <div class="bg-red-900/20 border-2 border-red-500/50 rounded-lg p-6 mb-8">
              <h2 class="text-2xl font-display text-red-300 mb-4">Important Notice</h2>
              <div class="space-y-3 text-parchment-200">
                <p class="leading-relaxed font-semibold">
                  Artificial University is NOT an accredited educational institution.
                </p>
                <p class="leading-relaxed">
                  This platform is an experimental project that uses artificial intelligence to
                  generate educational content. All courses, professors, departments, and lectures
                  on this site are AI-generated and created for entertainment and experimental
                  purposes only.
                </p>
                <p class="leading-relaxed">
                  This is an alpha-stage project in active development. Content may be inaccurate,
                  incomplete, or subject to change without notice. Do not rely on this content for
                  formal education, professional certification, or any official academic purpose.
                </p>
              </div>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">What This Is</h2>
              <p class="leading-relaxed">
                Artificial University is an experimental platform that explores what happens when we
                use large language models to generate complete educational content. The entire
                curriculum—from department structures to course syllabi, professor personalities,
                and lecture content—is created by AI systems.
              </p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">How It Works</h2>
              <p class="leading-relaxed">
                Using various AI models (including Claude, GPT, and others), the platform generates:
                courses across diverse academic fields, fictional professor profiles with distinct
                teaching styles and personalities, structured lecture content organized by topics
                and weeks, and text-to-speech audio versions of lectures using voice synthesis.
              </p>
              <p class="leading-relaxed mt-4">
                Users can create new courses, customize parameters, and explore AI-generated
                academic content. This is primarily a creative and technical experiment in automated
                content generation.
              </p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">What This Is NOT</h2>
              <p class="leading-relaxed">
                This platform does not offer real courses, accredited programs, academic credits,
                degrees or certificates, qualified instruction from human experts, or verified
                educational content. No one affiliated with this project is your teacher, mentor, or
                academic advisor.
              </p>
            </div>

            <div>
              <h2 class="text-2xl font-display text-parchment-100 mb-4">Alpha Status</h2>
              <p class="leading-relaxed">
                This project is in early alpha development. Expect bugs, incomplete features, and
                significant changes. The AI-generated content has not been reviewed for accuracy and
                may contain errors, biases, or outdated information. Use this platform at your own
                discretion and for entertainment purposes only.
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
