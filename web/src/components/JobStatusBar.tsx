import { createSignal, onCleanup, onMount, Show } from 'solid-js'
import { getJobsSummary, type JobStatus } from '../api/services/jobs-service'

type Summary = Partial<Record<JobStatus, number>>

const POLL_MS = 2000

export default function JobStatusBar() {
  const [summary, setSummary] = createSignal<Summary>({})
  const [err, setErr] = createSignal('')

  let timer: number | undefined

  const tick = async () => {
    try {
      const data = await getJobsSummary()
      setSummary(data)
      setErr('')
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'failed to fetch jobs')
    }
  }

  onMount(() => {
    void tick()
    timer = setInterval(() => void tick(), POLL_MS) as unknown as number
  })
  onCleanup(() => {
    if (timer) clearInterval(timer)
  })

  const totalActive = () => (summary().queued || 0) + (summary().running || 0)

  return (
    <div class="sticky top-0 z-30 bg-surface/80 backdrop-blur border-b border-border">
      <div class="mx-auto max-w-6xl px-3 py-2 flex items-center justify-between text-sm">
        <div class="flex items-center gap-3">
          <span class="font-semibold">Jobs</span>
          <Show when={totalActive() > 0} fallback={<span class="opacity-60">idle</span>}>
            <div class="flex items-center gap-2">
              <Show when={summary().queued}>
                <span class="rounded bg-muted px-2 py-0.5">queued: {summary().queued}</span>
              </Show>
              <Show when={summary().running}>
                <span class="rounded bg-primary/10 text-primary px-2 py-0.5">
                  running: {summary().running}
                </span>
              </Show>
            </div>
          </Show>
        </div>
        <div class="flex items-center gap-2 opacity-80">
          <Show when={summary().done}>
            <span class="rounded bg-secondary/10 text-secondary px-2 py-0.5">
              done: {summary().done}
            </span>
          </Show>
          <Show when={summary().failed}>
            <span class="rounded bg-danger/10 text-danger px-2 py-0.5">
              failed: {summary().failed}
            </span>
          </Show>
        </div>
      </div>
      <Show when={err()}>
        <div class="mx-auto max-w-6xl px-3 pb-2 text-xs text-danger">{err()}</div>
      </Show>
    </div>
  )
}
