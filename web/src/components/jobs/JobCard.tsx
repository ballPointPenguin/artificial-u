import { A } from '@solidjs/router'
import { createMemo, Show } from 'solid-js'
import type { JobRow } from '../../api/services/jobs-service'
import { getJobKindLabel } from '../../utils/job-management'
import { Badge, Button } from '../ui'
import {
  durationMsFromResult,
  formatDurationMs,
  formatShortRelative,
  jobParamsText,
  runningElapsedMs,
} from './job-feed'

interface JobCardProps {
  job: JobRow
  /** Reactive clock (ms) driving relative times and the live running duration. */
  now: number
  onShowError: (job: JobRow) => void
  onCancel: (job: JobRow) => void
}

export const STATUS_VARIANT: Record<
  JobRow['status'],
  'info' | 'warning' | 'success' | 'danger' | 'outline'
> = {
  queued: 'info',
  running: 'warning',
  done: 'success',
  failed: 'danger',
  cancelled: 'outline',
}

export default function JobCard(props: JobCardProps) {
  const isActive = () => props.job.status === 'queued' || props.job.status === 'running'

  const duration = createMemo(() => {
    if (props.job.status === 'running') {
      const elapsed = runningElapsedMs(props.job, props.now)
      return elapsed != null ? `${formatDurationMs(elapsed)}…` : null
    }
    const ms = props.job.duration_ms ?? durationMsFromResult(props.job.result)
    return ms != null ? formatDurationMs(ms) : null
  })

  const params = createMemo(() => jobParamsText(props.job))
  const showAttempts = () =>
    props.job.attempts > 1 || props.job.status === 'failed' || Boolean(props.job.last_error)

  return (
    <div class="arcane-card p-4 animate-fade-in">
      <div class="flex items-center gap-2">
        <Badge variant={STATUS_VARIANT[props.job.status]}>
          <Show when={props.job.status === 'running'}>
            <span class="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
          </Show>
          {props.job.status}
        </Badge>
        <span class="font-medium text-sm truncate">{getJobKindLabel(props.job.kind)}</span>
        <span class="text-xs text-muted">#{props.job.id}</span>
        <span class="ml-auto text-xs text-muted whitespace-nowrap">
          {formatShortRelative(props.job.created_at, props.now)}
        </span>
      </div>

      <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
        <Show when={props.job.model}>
          <span class="font-mono">{props.job.model}</span>
        </Show>
        <Show when={duration()}>
          <span title="Run time">{duration()}</span>
        </Show>
        <Show when={showAttempts()}>
          <span>
            attempt {props.job.attempts}/{props.job.max_attempts}
          </span>
        </Show>
      </div>

      <Show when={params() || props.job.last_error || isActive()}>
        <div class="mt-2 flex items-center gap-2 text-xs">
          <Show when={params()}>
            <Show
              when={props.job.link_path}
              fallback={<span class="text-muted truncate">{params()}</span>}
            >
              <A href={props.job.link_path as string} class="text-accent hover:underline truncate">
                {params()}
              </A>
            </Show>
          </Show>
          <Show when={props.job.last_error}>
            <button
              type="button"
              class="text-danger hover:underline cursor-pointer truncate max-w-[40%]"
              onClick={() => {
                props.onShowError(props.job)
              }}
            >
              {props.job.last_error}
            </button>
          </Show>
          <Show when={isActive()}>
            <span class="ml-auto">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  props.onCancel(props.job)
                }}
              >
                Cancel
              </Button>
            </span>
          </Show>
        </div>
      </Show>
    </div>
  )
}
