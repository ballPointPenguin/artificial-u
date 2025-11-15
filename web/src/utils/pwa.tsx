import { createSignal, onMount, Show } from 'solid-js'
import { useRegisterSW } from 'virtual:pwa-register/solid'
import { Button } from '../components/ui/Button'
import { Alert } from '../components/ui/Alert'

export function PWAUpdatePrompt() {
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
              <h3 class="font-semibold text-lg">Update Available</h3>
              <p class="text-sm opacity-90 mt-1">
                A new version of Artificial University is available. Reload to update.
              </p>
            </div>
            <div class="flex gap-2">
              <Button
                onClick={() => updateServiceWorker(true)}
                size="sm"
                variant="primary"
              >
                Update Now
              </Button>
              <Button onClick={() => setNeedRefresh(false)} size="sm" variant="ghost">
                Later
              </Button>
            </div>
          </div>
        </Alert>
      </div>
    </Show>
  )
}

export function InstallPWAPrompt() {
  const [deferredPrompt, setDeferredPrompt] = createSignal<any>(null)
  const [isVisible, setIsVisible] = createSignal(false)

  onMount(() => {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      setDeferredPrompt(e)
      setIsVisible(true)
    })

    window.addEventListener('appinstalled', () => {
      setDeferredPrompt(null)
      setIsVisible(false)
      console.log('PWA was installed')
    })
  })

  const handleInstall = async () => {
    const prompt = deferredPrompt()
    if (!prompt) return

    prompt.prompt()
    const { outcome } = await prompt.userChoice
    console.log(`User response to the install prompt: ${outcome}`)

    setDeferredPrompt(null)
    setIsVisible(false)
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
              <h3 class="font-semibold text-lg">Install App</h3>
              <p class="text-sm opacity-90 mt-1">
                Install Artificial University for quick access and offline use.
              </p>
            </div>
            <div class="flex gap-2">
              <Button onClick={handleInstall} size="sm" variant="primary">
                Install
              </Button>
              <Button onClick={handleDismiss} size="sm" variant="ghost">
                Not Now
              </Button>
            </div>
          </div>
        </Alert>
      </div>
    </Show>
  )
}
