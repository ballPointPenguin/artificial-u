import { Share2 } from 'lucide-solid'
import { type ComponentProps, createSignal, Show } from 'solid-js'
import { Button } from './Button.jsx'

type ShareStatus = 'idle' | 'copied' | 'failed'
type ShareLayout = 'inline' | 'stacked'

export interface ShareButtonProps {
  url?: string
  title?: string
  text?: string
  label?: string
  layout?: ShareLayout
  class?: string
  variant?: ComponentProps<typeof Button>['variant']
  size?: ComponentProps<typeof Button>['size']
}

export const ShareButton = (props: ShareButtonProps) => {
  const [status, setStatus] = createSignal<ShareStatus>('idle')

  const layout = () => props.layout ?? 'inline'

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      return
    } catch {
      // Clipboard API may fail in non-secure contexts or due to permissions.
      // Use a non-deprecated fallback that still lets the user copy.
      const ok = window.prompt('Copy this link:', text)
      if (ok === null) throw new Error('Copy cancelled')
    }
  }

  const onShare = async () => {
    const url = props.url
    if (!url) return

    try {
      // Prefer native share sheet when available
      if ('share' in navigator && typeof navigator.share === 'function') {
        await navigator.share({
          url,
          title: props.title,
          text: props.text,
        })
        setStatus('idle')
        return
      }

      await copyToClipboard(url)
      setStatus('copied')
      setTimeout(() => setStatus('idle'), 1500)
    } catch {
      setStatus('failed')
      setTimeout(() => setStatus('idle'), 1500)
    }
  }

  return (
    <Button
      variant={props.variant ?? 'outline'}
      size={props.size ?? 'sm'}
      class={[
        layout() === 'stacked'
          ? 'inline-flex flex-col items-center justify-center gap-1'
          : 'inline-flex items-center justify-center gap-2',
        props.class ?? '',
      ].join(' ')}
      onClick={() => void onShare()}
    >
      <Share2 class="h-4 w-4 shrink-0" />
      <span class={layout() === 'stacked' ? 'leading-none' : ''}>
        <Show when={status() === 'copied'} fallback={props.label ?? 'Share'}>
          Copied
        </Show>
        <Show when={status() === 'failed'}>Failed</Show>
      </span>
    </Button>
  )
}
