import { A } from '@solidjs/router'
import { createSignal, For, onCleanup, Show } from 'solid-js'
import {
  type CourseCodeAction,
  courseImportService,
  type ImportAnalysis,
  type ImportResolutions,
} from '../../api/services/course-import-service'
import { getJob, type JobRow } from '../../api/services/jobs-service'
import { Alert, Button } from '../../components/ui'

type Phase = 'pick' | 'review' | 'running' | 'done'

interface ImportResult {
  cancelled?: boolean
  course_id?: number
  course_code?: string
  course_title?: string
  topics_created?: number
  lectures_created?: number
  assets_uploaded?: number
  warnings?: string[]
}

const ASSET_LABELS: Record<string, string> = {
  audio: 'Lecture audio',
  transcripts: 'Transcripts',
  timelines: 'Caption timelines',
  lecture_images: 'Lecture images',
  course_image: 'Course image',
  professor_image: 'Professor image',
}

export default function AdminImport() {
  const [phase, setPhase] = createSignal<Phase>('pick')
  const [busy, setBusy] = createSignal(false)
  const [error, setError] = createSignal('')
  const [analysis, setAnalysis] = createSignal<ImportAnalysis | null>(null)
  const [job, setJob] = createSignal<JobRow | null>(null)

  const [codeAction, setCodeAction] = createSignal<CourseCodeAction>('rename')
  const [newCode, setNewCode] = createSignal('')
  const [professorChoice, setProfessorChoice] = createSignal<string>('')
  const [hidden, setHidden] = createSignal(false)

  let pollTimer: number | undefined
  onCleanup(() => {
    window.clearTimeout(pollTimer)
  })

  const plan = () => analysis()?.plan
  const conflict = () => plan()?.course_code_conflict ?? null

  const reset = () => {
    window.clearTimeout(pollTimer)
    setPhase('pick')
    setAnalysis(null)
    setJob(null)
    setError('')
    setCodeAction('rename')
    setNewCode('')
    setProfessorChoice('')
    setHidden(false)
  }

  const handleFile = async (file: File | undefined) => {
    if (!file) return
    setBusy(true)
    setError('')
    try {
      const result = await courseImportService.analyze(file)
      setAnalysis(result)
      setNewCode(result.plan.course_code_conflict?.suggested_code ?? '')
      const candidates = result.plan.professor.candidates ?? []
      setProfessorChoice(candidates.length > 0 ? String(candidates[0].id) : 'create')
      setPhase('review')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to read archive')
    } finally {
      setBusy(false)
    }
  }

  const poll = (jobId: number) => {
    pollTimer = window.setTimeout(() => {
      void getJob(jobId)
        .then((row) => {
          setJob(row)
          if (row.status === 'done' || row.status === 'failed' || row.status === 'cancelled') {
            setPhase('done')
          } else {
            poll(jobId)
          }
        })
        .catch(() => {
          poll(jobId)
        })
    }, 1500)
  }

  const buildResolutions = (): ImportResolutions => {
    const resolutions: ImportResolutions = { hidden: hidden() }
    if (conflict()) {
      resolutions.course_code = codeAction()
      if (codeAction() === 'rename') resolutions.new_code = newCode().trim()
    }
    if (plan()?.professor.action !== 'none') {
      if (professorChoice() === 'create') {
        resolutions.professor = 'create'
      } else if (professorChoice()) {
        resolutions.professor = 'reuse'
        resolutions.professor_id = Number(professorChoice())
      }
    }
    return resolutions
  }

  const canImport = () => !(conflict() && codeAction() === 'rename' && !newCode().trim())

  const handleImport = async () => {
    const current = analysis()
    if (!current) return
    setBusy(true)
    setError('')
    try {
      const row = await courseImportService.start(current.upload_key, buildResolutions())
      setJob(row)
      setPhase('running')
      poll(row.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start import')
    } finally {
      setBusy(false)
    }
  }

  const result = (): ImportResult | null => {
    const raw = job()?.result
    return raw && typeof raw === 'object' ? raw : null
  }

  return (
    <div class="container mx-auto max-w-3xl px-4 py-8 space-y-6">
      <div>
        <h2 class="font-display text-xl text-parchment-100">Import a course</h2>
        <p class="text-muted text-sm mt-1">
          Upload a course export (.zip) from this or another instance. You'll see what it contains
          and decide how to handle conflicts before anything is created.
        </p>
      </div>

      <Show when={error()}>
        <Alert variant="danger">{error()}</Alert>
      </Show>

      <Show when={phase() === 'pick'}>
        <div class="arcane-card p-6">
          <input
            type="file"
            accept=".zip,application/zip"
            disabled={busy()}
            onChange={(e) => void handleFile(e.currentTarget.files?.[0])}
            class="block w-full text-sm text-parchment-200"
          />
          <Show when={busy()}>
            <p class="text-muted text-sm mt-3">Uploading and analyzing…</p>
          </Show>
        </div>
      </Show>

      <Show when={phase() === 'review' && plan()}>
        {(p) => (
          <div class="space-y-4">
            <div class="arcane-card p-6 space-y-2">
              <h3 class="font-display text-lg text-parchment-100">
                {p().course.code} — {p().course.title}
              </h3>
              <p class="text-sm text-muted">
                {p().course.lectures} lectures in {p().course.topics} topics · format v
                {p().export_version}
                <Show when={p().exported_at}> · exported {p().exported_at?.slice(0, 10)}</Show>
              </p>
              <ul class="text-sm text-parchment-200 grid grid-cols-2 gap-x-6">
                <For each={Object.entries(ASSET_LABELS)}>
                  {([key, label]) => (
                    <li>
                      {label}: {p().assets[key] ?? 0}
                    </li>
                  )}
                </For>
              </ul>
              <Show when={p().tags.length > 0}>
                <p class="text-sm text-muted">Tags: {p().tags.join(', ')}</p>
              </Show>
            </div>

            <Show when={conflict()}>
              {(c) => (
                <div class="arcane-card p-6 space-y-3 border border-warning-border">
                  <h4 class="font-display text-parchment-100">
                    Course code {c().existing.code} already exists
                  </h4>
                  <p class="text-sm text-parchment-200">
                    <A href={`/courses/${String(c().existing.id)}`} class="underline">
                      {c().existing.title}
                    </A>{' '}
                    · {c().existing.lecture_count} lectures · {c().existing.status}
                    <Show when={c().existing.professor_name}> · {c().existing.professor_name}</Show>
                    <Show when={c().same_title}>
                      {' '}
                      — same title, this is probably an earlier copy of the same course.
                    </Show>
                  </p>
                  <label class="flex items-start gap-2 text-sm">
                    <input
                      type="radio"
                      name="code-action"
                      checked={codeAction() === 'rename'}
                      onChange={() => setCodeAction('rename')}
                    />
                    <span class="flex-1">
                      Import as a new course with code{' '}
                      <input
                        type="text"
                        value={newCode()}
                        onInput={(e) => setNewCode(e.currentTarget.value)}
                        onFocus={() => setCodeAction('rename')}
                        class="ml-1 w-40 rounded border border-border bg-surface px-2 py-0.5"
                      />
                      <span class="block text-muted">
                        Audio and images are re-keyed under the new code.
                      </span>
                    </span>
                  </label>
                  <label class="flex items-start gap-2 text-sm">
                    <input
                      type="radio"
                      name="code-action"
                      checked={codeAction() === 'replace'}
                      onChange={() => setCodeAction('replace')}
                    />
                    <span>
                      Replace the existing course
                      <span class="block text-muted">
                        The new copy is built first; the old course, its lectures and files are
                        deleted only after it succeeds.
                      </span>
                    </span>
                  </label>
                  <label class="flex items-center gap-2 text-sm">
                    <input
                      type="radio"
                      name="code-action"
                      checked={codeAction() === 'cancel'}
                      onChange={() => setCodeAction('cancel')}
                    />
                    Cancel
                  </label>
                </div>
              )}
            </Show>

            <Show when={p().professor.action !== 'none'}>
              <div class="arcane-card p-6 space-y-2">
                <h4 class="font-display text-parchment-100">Professor: {p().professor.name}</h4>
                <For each={p().professor.candidates ?? []}>
                  {(candidate) => (
                    <label class="flex items-center gap-2 text-sm">
                      <input
                        type="radio"
                        name="professor"
                        checked={professorChoice() === String(candidate.id)}
                        onChange={() => setProfessorChoice(String(candidate.id))}
                      />
                      Use existing: {candidate.name}
                      <Show when={candidate.title}> ({candidate.title})</Show>
                      <Show when={candidate.department}> · {candidate.department}</Show>
                    </label>
                  )}
                </For>
                <label class="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="professor"
                    checked={professorChoice() === 'create'}
                    onChange={() => setProfessorChoice('create')}
                  />
                  Create a new professor from the archive
                </label>
              </div>
            </Show>

            <div class="arcane-card p-6 space-y-1 text-sm text-parchment-200">
              <Show when={p().department.action !== 'none'}>
                <p>
                  Department {p().department.name} ({p().department.code}):{' '}
                  {p().department.action === 'match'
                    ? `matches existing (by ${p().department.match?.matched_by ?? 'name'})`
                    : 'will be created'}
                </p>
              </Show>
              <For each={p().voices}>
                {(v) => (
                  <p>
                    Voice {v.name ?? '(unnamed)'}:{' '}
                    {v.action === 'match'
                      ? 'matches existing'
                      : v.action === 'create'
                        ? 'will be added'
                        : 'cannot be matched, left unset'}
                  </p>
                )}
              </For>
              <Show when={p().connected_courses.found.length > 0}>
                <p>Linked to: {p().connected_courses.found.join(', ')}</p>
              </Show>
              <Show when={p().connected_courses.missing.length > 0}>
                <p class="text-muted">
                  Connected courses not on this instance (skipped):{' '}
                  {p().connected_courses.missing.join(', ')}
                </p>
              </Show>
              <label class="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  checked={hidden()}
                  onChange={(e) => setHidden(e.currentTarget.checked)}
                />
                Import as hidden (don't publish even if it was published at the source)
              </label>
            </div>

            <Show when={p().warnings.length > 0}>
              <Alert variant="warning">
                <ul class="list-disc pl-5 text-sm">
                  <For each={p().warnings}>{(w) => <li>{w}</li>}</For>
                </ul>
              </Alert>
            </Show>

            <div class="flex gap-3">
              <Button onClick={() => void handleImport()} disabled={busy() || !canImport()}>
                {conflict() && codeAction() === 'cancel' ? 'Cancel import' : 'Import'}
              </Button>
              <Button variant="outline" onClick={reset} disabled={busy()}>
                Start over
              </Button>
            </div>
          </div>
        )}
      </Show>

      <Show when={phase() === 'running'}>
        <div class="arcane-card p-6">
          <p class="text-parchment-200">
            Importing… (job #{job()?.id}, {job()?.status})
          </p>
          <A href="/admin/jobs" class="text-sm underline text-muted">
            View in jobs
          </A>
        </div>
      </Show>

      <Show when={phase() === 'done'}>
        <div class="space-y-4">
          <Show when={job()?.status === 'failed'}>
            <Alert variant="danger">Import failed: {job()?.last_error ?? 'unknown error'}</Alert>
          </Show>
          <Show when={job()?.status === 'done' && result()?.cancelled}>
            <Alert variant="info">Import cancelled. Nothing was changed.</Alert>
          </Show>
          <Show when={job()?.status === 'done' && result()?.course_id}>
            <Alert variant="success">
              Imported{' '}
              <A href={`/courses/${String(result()?.course_id)}`} class="underline">
                {result()?.course_code} — {result()?.course_title}
              </A>
              : {result()?.lectures_created} lectures, {result()?.topics_created} topics,{' '}
              {result()?.assets_uploaded} files.
            </Alert>
            <Show when={(result()?.warnings ?? []).length > 0}>
              <Alert variant="warning">
                <ul class="list-disc pl-5 text-sm">
                  <For each={result()?.warnings}>{(w) => <li>{w}</li>}</For>
                </ul>
              </Alert>
            </Show>
          </Show>
          <Button variant="outline" onClick={reset}>
            Import another
          </Button>
        </div>
      </Show>
    </div>
  )
}
