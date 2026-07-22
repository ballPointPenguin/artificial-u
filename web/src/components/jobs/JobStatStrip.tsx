import { For, Show } from 'solid-js'
import type { JobStatus, JobsSummary } from '../../api/services/jobs-service'

interface JobStatStripProps {
  summary: JobsSummary | undefined
  activeStatus: JobStatus | undefined
  onToggleStatus: (status: JobStatus) => void
}

const STATUSES: Array<{ status: JobStatus; label: string; accent: string }> = [
  { status: 'queued', label: 'Queued', accent: 'text-info' },
  { status: 'running', label: 'Running', accent: 'text-warning' },
  { status: 'done', label: 'Done', accent: 'text-success' },
  { status: 'failed', label: 'Failed', accent: 'text-danger' },
  { status: 'cancelled', label: 'Cancelled', accent: 'text-muted' },
]

function formatWaitSeconds(seconds: number | undefined): string {
  if (seconds == null) return '-'
  if (seconds < 90) return `${String(Math.round(seconds))}s`
  return `${String(Math.round(seconds / 60))}m`
}

/**
 * Counts-by-status tiles that double as the status filter, plus a small
 * queue-health line (failures in the last hour, average queued wait).
 */
export default function JobStatStrip(props: JobStatStripProps) {
  return (
    <div class="mb-4">
      <div class="grid grid-cols-3 sm:grid-cols-5 gap-2">
        <For each={STATUSES}>
          {(entry) => (
            <button
              type="button"
              onClick={() => {
                props.onToggleStatus(entry.status)
              }}
              class="arcane-card p-3 text-center cursor-pointer transition-all"
              classList={{
                'ring-2 ring-primary': props.activeStatus === entry.status,
                'opacity-60':
                  props.activeStatus !== undefined && props.activeStatus !== entry.status,
              }}
              aria-pressed={props.activeStatus === entry.status}
            >
              <div class={`stat-number-sm ${entry.accent}`}>
                {props.summary?.counts[entry.status] ?? 0}
              </div>
              <div class="section-label mt-1">{entry.label}</div>
            </button>
          )}
        </For>
      </div>
      <Show when={props.summary}>
        {(summary) => (
          <div class="mt-2 text-xs text-muted flex gap-4">
            <span
              classList={{ 'text-danger': summary().failed_last_hour > 0 }}
              title="Jobs that failed in the last hour"
            >
              Failed 1h: {summary().failed_last_hour}
            </span>
            <span title="Average wait of currently queued jobs">
              Avg wait: {formatWaitSeconds(summary().avg_wait_seconds)}
            </span>
          </div>
        )}
      </Show>
    </div>
  )
}
