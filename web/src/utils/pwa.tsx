import { useRegisterSW } from 'virtual:pwa-register/solid'
import { createSignal, onMount, Show } from 'solid-js'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { useI18n } from '../i18n/index.js'

// Type for the beforeinstallprompt event
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

export function PWAUpdatePrompt() {
  const { t } = useI18n()
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(registration: ServiceWorkerRegistration | undefined) {
      if (registration) {
        console.log('SW Registered:', registration)
      }
    },
    onRegisterError(error: Error) {
      console.error('SW registration error:', error)
    },
  })

  return (
    <Show when={needRefresh()}>
      <div class="fixed bottom-4 right-4 z-50 max-w-md animate-slide-up">
        <Alert variant="info">
          <div class="flex flex-col gap-3">
            <div>
              <h3 class="font-semibold text-lg">{t().pwa.updateAvailable}</h3>
              <p class="text-sm opacity-90 mt-1">{t().pwa.updateMessage}</p>
            </div>
            <div class="flex gap-2">
              <Button
                onClick={() => {
                  void updateServiceWorker(true)
                }}
                size="sm"
                variant="primary"
              >
                {t().pwa.updateNow}
              </Button>
              <Button onClick={() => setNeedRefresh(false)} size="sm" variant="ghost">
                {t().pwa.later}
              </Button>
            </div>
          </div>
        </Alert>
      </div>
    </Show>
  )
}

// Simple mobile detection based on screen width and touch capability
const isMobileDevice = () => {
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
  const isMobileWidth = window.innerWidth < 768
  return hasTouch && isMobileWidth
}

export function InstallPWAPrompt() {
  const { t } = useI18n()
  const [deferredPrompt, setDeferredPrompt] = createSignal<BeforeInstallPromptEvent | null>(null)
  const [isVisible, setIsVisible] = createSignal(false)

  onMount(() => {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      // Only show install prompt on mobile devices
      if (isMobileDevice()) {
        setIsVisible(true)
      }
    })

    window.addEventListener('appinstalled', () => {
      setDeferredPrompt(null)
      setIsVisible(false)
      console.log('PWA was installed')
    })
  })

  const handleInstall = () => {
    const prompt = deferredPrompt()
    if (!prompt) return

    void prompt
      .prompt()
      .then(() => prompt.userChoice)
      .then(({ outcome }) => {
        console.log(`User response to the install prompt: ${outcome}`)
        setDeferredPrompt(null)
        setIsVisible(false)
      })
      .catch((error: unknown) => {
        console.error('Install prompt error:', error)
      })
  }

  const handleDismiss = () => {
    setIsVisible(false)
  }

  return (
    <Show when={isVisible()}>
      <div class="fixed bottom-4 left-4 z-50 max-w-md animate-slide-up">
        <Alert variant="success">
          <div class="flex flex-col gap-3">
            <div>
              <h3 class="font-semibold text-lg">{t().pwa.installApp}</h3>
              <p class="text-sm opacity-90 mt-1">{t().pwa.installMessage}</p>
            </div>
            <div class="flex gap-2">
              <Button onClick={handleInstall} size="sm" variant="primary">
                {t().pwa.install}
              </Button>
              <Button onClick={handleDismiss} size="sm" variant="ghost">
                {t().pwa.notNow}
              </Button>
            </div>
          </div>
        </Alert>
      </div>
    </Show>
  )
}
