// src/components/AnimatedLayout.tsx
import { type JSX, createSignal, onCleanup, onMount } from 'solid-js'
import { NavBar } from './NavBar'
import { ThemeSwitcher } from './ThemeSwitcher'

interface AnimatedLayoutProps {
  children: JSX.Element
  showParticles?: boolean
  showGradient?: boolean
  showNavBar?: boolean
  showThemeSwitcher?: boolean
}

export function AnimatedLayout(props: AnimatedLayoutProps) {
  let canvasRef: HTMLCanvasElement | undefined
  let animationFrameId: number
  const [mounted, setMounted] = createSignal(false)

  // Particle system for background effect
  class Particle {
    x: number
    y: number
    size: number
    speedX: number
    speedY: number
    color: string
    opacity: number
    life: number
    maxLife: number

    constructor(canvas: HTMLCanvasElement) {
      this.x = Math.random() * canvas.width
      this.y = Math.random() * canvas.height
      this.size = Math.random() * 2 + 0.5
      this.speedX = Math.random() * 0.5 - 0.25
      this.speedY = Math.random() * 0.5 - 0.25

      // Colors that match our dark academia and vaporwave themes
      const colors = [
        'rgba(194, 151, 71, ', // parchment-500
        'rgba(138, 86, 255, ', // mystic-500
        'rgba(176, 153, 129, ', // arcanum-400
        'rgba(208, 151, 254, ', // nebula-400
      ]

      this.color = colors[Math.floor(Math.random() * colors.length)]
      this.opacity = 0
      this.life = 0
      this.maxLife = Math.random() * 100 + 100
    }

    update() {
      this.x += this.speedX
      this.y += this.speedY

      // Fade in and out based on life
      if (this.life < 20) {
        this.opacity += 0.05
      } else if (this.life > this.maxLife - 20) {
        this.opacity -= 0.05
      }
      this.opacity = Math.max(0, Math.min(0.7, this.opacity))

      this.life++
    }

    draw(ctx: CanvasRenderingContext2D) {
      ctx.beginPath()
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
      ctx.fillStyle = `${this.color}${this.opacity.toString()})`
      ctx.fill()
    }

    isDead() {
      return this.life >= this.maxLife
    }
  }

  // Initialize canvas and animation
  onMount(() => {
    setMounted(true)

    if ((!props.showParticles && props.showParticles !== undefined) || !canvasRef) return

    const canvas = canvasRef
    const ctx = canvas.getContext('2d')

    if (!ctx) return

    // Resize canvas to window size
    const handleResize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    window.addEventListener('resize', handleResize)
    handleResize()

    // Create particles
    const particles: Particle[] = []
    const particleCount = Math.min(
      Math.floor((window.innerWidth * window.innerHeight) / 10000),
      100
    )

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle(canvas))
    }

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Update and draw particles
      for (let i = particles.length - 1; i >= 0; i--) {
        particles[i].update()
        particles[i].draw(ctx)

        // Remove dead particles and add new ones
        if (particles[i].isDead()) {
          particles.splice(i, 1)
          particles.push(new Particle(canvas))
        }
      }

      // Connect particles with lines if they're close enough
      ctx.lineWidth = 0.3
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const distance = Math.sqrt(dx * dx + dy * dy)

          if (distance < 100) {
            ctx.beginPath()
            ctx.strokeStyle = `rgba(194, 151, 71, ${(0.2 * (1 - distance / 100)).toString()})` // parchment color
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.stroke()
          }
        }
      }

      animationFrameId = requestAnimationFrame(animate)
    }

    animate()

    // Cleanup
    onCleanup(() => {
      window.removeEventListener('resize', handleResize)
      cancelAnimationFrame(animationFrameId)
    })
  })

  return (
    <div class="min-h-screen flex flex-col relative overflow-hidden">
      {/* Particle effect background */}
      {(props.showParticles === undefined || props.showParticles) && (
        <canvas ref={canvasRef} class="fixed top-0 left-0 w-full h-full pointer-events-none z-0" />
      )}

      {/* Gradient background */}
      {(props.showGradient === undefined || props.showGradient) && (
        <div class="fixed inset-0 z-0 bg-arcanum-950">
          <div class="absolute inset-0 opacity-20">
            <div
              class="absolute top-1/4 left-1/4 w-1/2 h-1/2 bg-nebula-800/10 rounded-full filter blur-3xl animate-wisps"
              style={{ 'animation-delay': '0s' }}
            />
            <div
              class="absolute top-1/3 left-1/3 w-1/3 h-2/3 bg-vaporwave-800/10 rounded-full filter blur-3xl animate-wisps"
              style={{ 'animation-delay': '1s' }}
            />
            <div
              class="absolute top-1/2 left-1/2 w-1/2 h-1/3 bg-mystic-800/10 rounded-full filter blur-3xl animate-wisps"
              style={{ 'animation-delay': '2s' }}
            />
          </div>
        </div>
      )}

      {/* Content */}
      <div class="relative z-10 flex flex-col min-h-screen">
        {(props.showNavBar === undefined || props.showNavBar) && <NavBar />}

        <main class="flex-grow">{props.children}</main>
      </div>

      {/* Theme switcher */}
      {(props.showThemeSwitcher === undefined || props.showThemeSwitcher) && mounted() && (
        <ThemeSwitcher />
      )}
    </div>
  )
}
