import { createMemo, Show } from 'solid-js'
import type { JobKindStat } from '../../api/services/jobs-service'
import { getJobKindLabel, JOB_KINDS } from '../../utils/job-management'
import { Select } from '../ui'
import { formatDurationMs } from './job-feed'

interface JobFiltersProps {
  kind: string | undefined
  onKindChange: (kind: string | undefined) => void
  kindStats: JobKindStat[] | undefined
}

const ALL_KINDS = ''

/**
 * Kind filter with recent per-kind stats for the selected kind — the numbers
 * used to estimate how long a currently running job will take.
 */
export default function JobFilters(props: JobFiltersProps) {
  const options = createMemo(() => [
    { value: ALL_KINDS, label: 'All kinds' },
    ...JOB_KINDS.map((kind) => ({ value: kind, label: getJobKindLabel(kind) })),
  ])

  const selectedStat = createMemo(() => {
    if (!props.kind) return undefined
    return props.kindStats?.find((stat) => stat.kind === props.kind)
  })

  return (
    <div class="mb-4">
      <Select
        name="job-kind-filter"
        label="Filter by job kind"
        options={options()}
        value={props.kind ?? ALL_KINDS}
        onChange={(value) => {
          props.onKindChange(value ? String(value) : undefined)
        }}
        placeholder="All kinds"
      />
      <Show when={selectedStat()}>
        {(stat) => (
          <div class="mt-1.5 text-xs text-muted">
            Last 24h: {stat().count} jobs · avg {formatDurationMs(stat().avg_duration_ms)} · p50{' '}
            {formatDurationMs(stat().p50_duration_ms)}
          </div>
        )}
      </Show>
    </div>
  )
}
