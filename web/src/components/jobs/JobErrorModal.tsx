import * as Dialog from '@kobalte/core/dialog'
import { A } from '@solidjs/router'
import { createSignal, onCleanup, Show } from 'solid-js'
import type { JobRow } from '../../api/services/jobs-service'
import { formatLocalDateTimeISO } from '../../utils/formatDate'
import { getJobKindLabel } from '../../utils/job-management'
import { Badge, Button } from '../ui'
import { STATUS_VARIANT } from './JobCard'
import { durationMsFromResult, formatDurationMs, jobParamsText } from './job-feed'

interface JobErrorModalProps {
  job: JobRow | null
  onClose: () => void
}

export default function JobErrorModal(props: JobErrorModalProps) {
  const [copied, setCopied] = createSignal(false)
  let copiedTimer: ReturnType<typeof setTimeout> | null = null
  onCleanup(() => {
    if (copiedTimer) clearTimeout(copiedTimer)
  })

  const copyError = (text: string) => {
    void navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      if (copiedTimer) clearTimeout(copiedTimer)
      copiedTimer = setTimeout(() => {
        setCopied(false)
      }, 1500)
    })
  }

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) props.onClose()
  }

  return (
    <Dialog.Root open={props.job !== null} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <Show when={props.job}>
            {(job) => {
              const durationMs = () => job().duration_ms ?? durationMsFromResult(job().result)
              const params = () => jobParamsText(job())
              return (
                <Dialog.Content class="arcane-card max-w-2xl max-h-[85vh] w-full flex flex-col shadow-xl rounded-lg overflow-hidden">
                  <div class="p-4 sm:p-6 border-b border-border">
                    <div class="flex items-center gap-2 min-w-0">
                      <Badge variant={STATUS_VARIANT[job().status]}>{job().status}</Badge>
                      <Dialog.Title class="text-lg font-display truncate">
                        {getJobKindLabel(job().kind)}
                      </Dialog.Title>
                      <span class="text-sm text-muted whitespace-nowrap">#{job().id}</span>
                      <span class="ml-auto">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            props.onClose()
                          }}
                        >
                          ✕
                        </Button>
                      </span>
                    </div>
                    <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                      <Show when={job().model}>
                        <span class="font-mono">{job().model}</span>
                      </Show>
                      <span>
                        attempt {job().attempts}/{job().max_attempts}
                      </span>
                      <Show when={durationMs() != null}>
                        <span title="Run time">{formatDurationMs(durationMs())}</span>
                      </Show>
                      <Show when={job().updated_at}>
                        <span title="Last update">
                          {formatLocalDateTimeISO(job().updated_at as string)}
                        </span>
                      </Show>
                    </div>
                    <Show when={params()}>
                      <div class="mt-1.5 text-xs">
                        <Show
                          when={job().link_path}
                          fallback={<span class="text-muted">{params()}</span>}
                        >
                          <A href={job().link_path as string} class="text-accent hover:underline">
                            {params()} →
                          </A>
                        </Show>
                      </div>
                    </Show>
                  </div>
                  <Dialog.Description
                    as="div"
                    class="p-4 sm:p-6 overflow-auto flex-1 min-h-0 text-left"
                  >
                    <div class="bg-danger-bg border border-danger-border rounded-sm p-4 overflow-x-auto">
                      <pre class="text-xs font-mono whitespace-pre-wrap break-words">
                        {job().last_error || 'No error message available'}
                      </pre>
                    </div>
                  </Dialog.Description>
                  <div class="flex justify-end gap-2 p-4 sm:p-6 border-t border-border">
                    <Show when={job().last_error}>
                      <Button
                        variant="outline"
                        onClick={() => {
                          copyError(job().last_error as string)
                        }}
                      >
                        {copied() ? 'Copied ✓' : 'Copy error'}
                      </Button>
                    </Show>
                    <Button
                      variant="secondary"
                      onClick={() => {
                        props.onClose()
                      }}
                    >
                      Close
                    </Button>
                  </div>
                </Dialog.Content>
              )
            }}
          </Show>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
