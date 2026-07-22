import { Show } from 'solid-js'
import type { JobRow } from '../../api/services/jobs-service'
import { Button } from '../ui'

interface JobErrorModalProps {
  job: JobRow | null
  onClose: () => void
}

export default function JobErrorModal(props: JobErrorModalProps) {
  return (
    <Show when={props.job}>
      {(job) => (
        <div
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => {
            props.onClose()
          }}
        >
          <div
            class="arcane-card max-w-3xl max-h-[80vh] w-full mx-4 overflow-hidden flex flex-col"
            onClick={(e) => {
              e.stopPropagation()
            }}
          >
            <div class="flex items-center justify-between p-4 sm:p-6 border-b border-border">
              <h2 class="text-xl font-display">
                Job Error - {job().kind} #{job().id}
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  props.onClose()
                }}
              >
                ✕
              </Button>
            </div>
            <div class="p-4 sm:p-6 overflow-auto">
              <pre class="text-xs font-mono bg-muted/50 p-4 rounded overflow-x-auto whitespace-pre-wrap break-words">
                {job().last_error || 'No error message available'}
              </pre>
            </div>
            <div class="flex justify-end gap-2 p-4 sm:p-6 border-t border-border">
              <Button
                variant="secondary"
                onClick={() => {
                  props.onClose()
                }}
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </Show>
  )
}
