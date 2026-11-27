import { createRoot, createSignal, flush } from 'solid-js'
import { describe, expect, it, vi } from 'vitest'
import { createResource } from './create-resource.js'

describe('createResource', () => {
  it('does not refetch when a sibling form field changes but the source key is unchanged', async () => {
    const fetcher = vi.fn((key: string) => Promise.resolve(`data:${key}`))

    let setForm!: (v: { departmentId: number; title: string }) => void

    const stop = createRoot((disposeRoot) => {
      const [form, set] = createSignal({ departmentId: 3, title: 'A' })
      setForm = set
      createResource(() => String(form().departmentId), fetcher)
      return disposeRoot
    })

    flush()
    await vi.waitFor(() => {
      expect(fetcher).toHaveBeenCalledTimes(1)
    })

    setForm({ departmentId: 3, title: 'Changed title after generation' })
    flush()
    await Promise.resolve()
    await Promise.resolve()
    expect(fetcher).toHaveBeenCalledTimes(1)

    setForm({ departmentId: 4, title: 'Other dept' })
    flush()
    await vi.waitFor(() => {
      expect(fetcher).toHaveBeenCalledTimes(2)
    })

    stop()
  })

  it('does not refetch for shallow-equal object sources when sibling fields change', async () => {
    const fetcher = vi.fn((src: { departmentId: number; authReady: boolean }) =>
      Promise.resolve(src)
    )

    let setForm!: (v: { departmentId: number; title: string }) => void
    let setAuthLoading!: (v: boolean) => void

    const stop = createRoot((disposeRoot) => {
      const [form, set] = createSignal({ departmentId: 3, title: 'A' })
      const [authLoading, setAuth] = createSignal(false)
      setForm = set
      setAuthLoading = setAuth
      createResource(
        () => ({
          departmentId: form().departmentId,
          authReady: !authLoading(),
        }),
        fetcher
      )
      return disposeRoot
    })

    flush()
    await vi.waitFor(() => {
      expect(fetcher).toHaveBeenCalledTimes(1)
    })

    setForm({ departmentId: 3, title: 'Syllabus filled in' })
    flush()
    await Promise.resolve()
    await Promise.resolve()
    expect(fetcher).toHaveBeenCalledTimes(1)

    setAuthLoading(true)
    flush()
    await vi.waitFor(() => {
      expect(fetcher).toHaveBeenCalledTimes(2)
    })

    stop()
  })
})
