import { Button } from '@kobalte/core/button'

interface HeroProps {
  title?: string
  subtitle?: string
  buttonText?: string
  buttonLink?: string
}

export function Hero(props: HeroProps) {
  return (
    <div class="relative min-h-screen flex items-center justify-center">
      {/* Content */}
      <div class="relative z-10 text-center px-4 sm:px-6 lg:px-8 max-w-5xl">
        <h1 class="text-5xl sm:text-6xl md:text-7xl font-display text-parchment-200 tracking-wider leading-tight mb-6 text-shadow-golden">
          {props.title}
        </h1>
        <p class="text-xl sm:text-2xl md:text-3xl font-serif text-parchment-100 mb-12">
          {props.subtitle}
        </p>
        <Button class="inline-block px-8 py-3 border-2 border-parchment-400 text-parchment-100 bg-arcanum-900/50 hover:bg-arcanum-800/50 transition-colors duration-300 rounded font-serif tracking-wider uppercase text-shadow-golden">
          <a href={props.buttonLink}>{props.buttonText}</a>
        </Button>

        {/* Decorative elements */}
        <div class="absolute -bottom-10 left-1/2 transform -translate-x-1/2 w-16 h-16 flex items-center justify-center">
          <div class="w-8 h-8 border-b-2 border-r-2 border-parchment-300/50 transform rotate-45 animate-bounce opacity-70" />
        </div>
      </div>
    </div>
  )
}
