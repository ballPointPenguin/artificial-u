/**
 * Solid 2-compatible stand-in for Solid 1's createResource.
 *
 * Prefer migrating call sites to async createMemo + <Loading>/<Errored> over time.
 * This helper keeps the familiar () / .loading / .error / refetch / mutate shape on
 * Solid 2's staged-write + split-effect model.
 */
import { createEffect, createSignal, type Accessor, type Setter } from 'solid-js'

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

  const [data, setData] = createSignal<T | undefined>(undefined)
  const [error, setError] = createSignal<unknown>(undefined)
  const [loading, setLoading] = createSignal(true)
  const [tick, setTick] = createSignal(0)
  const [refetching, setRefetching] = createSignal<unknown>(false)

  let currentRequest = 0

  createEffect(
    () => {
      tick()
      return source()
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
      const previous = data()
      const isRefresh = refetching() !== false
      setLoading(true)
      if (!isRefresh) {
        setError(undefined)
      }

      let cancelled = false
      Promise.resolve()
        .then(() =>
          fetcher(src as S, {
            value: previous,
            refetching: refetching(),
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
          (err) => {
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
