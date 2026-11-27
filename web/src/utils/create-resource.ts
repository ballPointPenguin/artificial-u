/**
 * Solid 2-compatible stand-in for Solid 1's createResource.
 *
 * Prefer migrating call sites to async createMemo + <Loading>/<Errored> over time.
 * This helper keeps the familiar () / .loading / .error / refetch / mutate shape on
 * Solid 2's staged-write + split-effect model.
 *
 * Important Solid 2 detail: createEffect apply runs whenever compute re-runs, even
 * when the returned value is unchanged. Source accessors often read a whole form
 * signal (e.g. formData().department_id) — any sibling field write would re-fire
 * the fetch. We memoize the source with shallow equality so apply only runs when
 * the source value actually changes (or refetch bumps `tick`).
 */
import {
  type Accessor,
  createEffect,
  createMemo,
  createSignal,
  type Setter,
  untrack,
} from 'solid-js'

export type ResourceSource<S> = S | false | null | undefined

export type ResourceFetcher<S, T> = (
  source: S,
  info: { value: T | undefined; refetching: unknown }
) => Promise<T> | T

export type Resource<T> = {
  (): T | undefined
  loading: boolean
  error: unknown
  latest: T | undefined
  state: 'unresolved' | 'pending' | 'ready' | 'refreshing' | 'errored'
}

export type ResourceActions<T> = {
  refetch: (info?: unknown) => T | Promise<T | undefined> | undefined | Promise<undefined>
  mutate: Setter<T | undefined>
}

export type ResourceReturn<T> = [Resource<T>, ResourceActions<T>]

function isSourceInactive(source: unknown): source is false | null | undefined {
  return source === false || source === null || source === undefined
}

/** Shallow equality so object sources like `{ page, size }` do not refetch on new refs. */
function sourceEquals(a: unknown, b: unknown): boolean {
  if (Object.is(a, b)) return true
  if (
    typeof a !== 'object' ||
    a === null ||
    typeof b !== 'object' ||
    b === null ||
    Array.isArray(a) ||
    Array.isArray(b)
  ) {
    return false
  }
  const ao = a as Record<string, unknown>
  const bo = b as Record<string, unknown>
  const keys = Object.keys(ao)
  if (keys.length !== Object.keys(bo).length) return false
  return keys.every((key) => Object.is(ao[key], bo[key]))
}

export function createResource<T>(fetcher: ResourceFetcher<true, T>): ResourceReturn<T>
export function createResource<T, S>(
  source: Accessor<ResourceSource<S>>,
  fetcher: ResourceFetcher<S, T>
): ResourceReturn<T>
export function createResource<T, S>(
  sourceOrFetcher: Accessor<ResourceSource<S>> | ResourceFetcher<true, T>,
  maybeFetcher?: ResourceFetcher<S, T>
): ResourceReturn<T> {
  const hasSource = typeof maybeFetcher === 'function'
  const source = hasSource
    ? (sourceOrFetcher as Accessor<ResourceSource<S>>)
    : () => true as unknown as ResourceSource<S>
  const fetcher = (hasSource ? maybeFetcher : sourceOrFetcher) as ResourceFetcher<S, T>

  // ownedWrite: effect apply intentionally updates these resource signals
  const [data, setData] = createSignal<T | undefined>(undefined, { ownedWrite: true })
  const [error, setError] = createSignal<unknown>(undefined, { ownedWrite: true })
  const [loading, setLoading] = createSignal(true, { ownedWrite: true })
  const [tick, setTick] = createSignal(0, { ownedWrite: true })
  const [refetching, setRefetching] = createSignal<unknown>(false, { ownedWrite: true })

  let currentRequest = 0

  // Stabilize the source so sibling signal writes do not re-run apply.
  const sourceValue = createMemo(() => source(), { equals: sourceEquals })

  createEffect(
    () => {
      tick()
      return sourceValue()
    },
    (src) => {
      if (isSourceInactive(src)) {
        setData(undefined)
        setError(undefined)
        setLoading(false)
        setRefetching(false)
        return
      }

      const requestId = ++currentRequest
      const previous = untrack(data)
      const isRefresh = untrack(refetching) !== false
      setLoading(true)
      if (!isRefresh) {
        setError(undefined)
      }

      let cancelled = false
      Promise.resolve()
        .then(() =>
          fetcher(src, {
            value: previous,
            refetching: untrack(refetching),
          })
        )
        .then(
          (value) => {
            if (cancelled || requestId !== currentRequest) return
            setData(() => value)
            setError(undefined)
            setLoading(false)
            setRefetching(false)
          },
          (err: unknown) => {
            if (cancelled || requestId !== currentRequest) return
            setError(() => err)
            setLoading(false)
            setRefetching(false)
          }
        )

      return () => {
        cancelled = true
      }
    }
  )

  // Accessor intentionally closes over reactive data(); Solid ESLint can't see that.
  // eslint-disable-next-line solid/reactivity -- resource() is the public reactive reader
  const resource = (() => data()) as Resource<T>
  Object.defineProperties(resource, {
    loading: {
      get: () => loading(),
      enumerable: true,
    },
    error: {
      get: () => error(),
      enumerable: true,
    },
    latest: {
      get: () => data(),
      enumerable: true,
    },
    state: {
      get: () => {
        if (error() != null) return 'errored'
        if (loading()) return data() === undefined ? 'pending' : 'refreshing'
        if (data() === undefined) return 'unresolved'
        return 'ready'
      },
      enumerable: true,
    },
  })

  const refetch = (info: unknown = true) => {
    setRefetching(() => info)
    setTick((n) => n + 1)
    return data()
  }

  return [resource, { refetch, mutate: setData }]
}
