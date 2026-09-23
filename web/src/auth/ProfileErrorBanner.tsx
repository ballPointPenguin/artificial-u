import { createSignal, Show } from 'solid-js'
import { Button } from '../components/ui/Button'
import { useTranslations } from '../i18n'
import { useAuth } from './AuthProvider'

/**
 * Shown when the user is signed in but their student profile (and therefore
 * their role) couldn't be loaded. Without it, role-gated UI just silently
 * disappears, which looks like a permissions problem rather than an error.
 */
export function ProfileErrorBanner() {
  const auth = useAuth()
  const t = useTranslations()
  const [retrying, setRetrying] = createSignal(false)

  const retry = async () => {
    setRetrying(true)
    try {
      await auth.refresh()
    } finally {
      setRetrying(false)
    }
  }

  return (
    <Show when={auth.isAuthenticated() && auth.profileError()}>
      <div
        role="alert"
        class="flex flex-wrap items-center justify-center gap-3 border-b border-error-border bg-error-surface px-4 py-2 text-sm text-error-text"
      >
        <span>{t().profile.loadFailedBanner}</span>
        <Button variant="secondary" size="sm" onClick={() => void retry()} disabled={retrying()}>
          {t().common.retry}
        </Button>
      </div>
    </Show>
  )
}
