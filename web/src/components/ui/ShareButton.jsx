import { Share2 } from 'lucide-solid'
import { createSignal, Show } from 'solid-js'
import { Button } from './Button.jsx'

export const ShareButton = (props) => {
  const [status, setStatus] = createSignal('idle') // idle | copied | failed

  const layout = () => props.layout ?? 'inline' // inline | stacked

  const copyToClipboard = async (text) => {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return
    }

    // Fallback for older browsers / non-secure contexts
    const el = document.createElement('textarea')
    el.value = text
    el.setAttribute('readonly', '')
    el.style.position = 'absolute'
    el.style.left = '-9999px'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }

  const onShare = async () => {
    const url = props.url
    if (!url) return

    try {
      // Prefer native share sheet when available
      if (navigator.share) {
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

