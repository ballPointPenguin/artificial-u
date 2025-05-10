import { Button } from './Button'
import { A } from '@solidjs/router'

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
        <h1 class="text-5xl sm:text-6xl md:text-7xl font-display text-foreground tracking-wider leading-tight mb-6 text-shadow-golden">
          {props.title}
        </h1>
        <p class="text-xl sm:text-2xl md:text-3xl font-serif text-muted mb-12">{props.subtitle}</p>
        {props.buttonLink && (
          <A href={props.buttonLink}>
            <Button variant="primary" size="lg" class="text-shadow-golden">
              {props.buttonText}
            </Button>
          </A>
        )}

        {/* Decorative elements */}
        <div class="absolute -bottom-10 left-1/2 transform -translate-x-1/2 w-16 h-16 flex items-center justify-center">
          <div class="w-8 h-8 border-b-2 border-r-2 border-muted/50 transform rotate-45 animate-bounce opacity-70" />
        </div>
      </div>
    </div>
  )
}
