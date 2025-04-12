import { Show, createResource, createSignal, onMount } from 'solid-js'
import {
  type APIInfo,
  ApiError,
  type HealthCheckResponse,
  getApiInfo,
  getHealthStatus,
} from '../api'

const ApiInfo = () => {
  const [info, { refetch: refetchInfo }] = createResource<APIInfo>(getApiInfo)
  const [health, { refetch: refetchHealth }] =
    createResource<HealthCheckResponse>(getHealthStatus)
  const [error, setError] = createSignal<string | null>(null)

  onMount(() => {
    // Clear any previous errors when mounting
    setError(null)
  })

  const handleRefresh = () => {
    setError(null)
    try {
      void refetchInfo()
      void refetchHealth()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`API Error: ${err.message}`)
      } else {
        setError(
          `Unexpected error: ${err instanceof Error ? err.message : String(err)}`
        )
      }
    }
  }

  return (
    <div class="p-4 bg-gray-800 rounded-lg shadow-lg">
      <h2 class="text-2xl font-bold mb-4 text-white">API Connection Status</h2>

      {/* Error message */}
      <Show when={error()}>
        <div class="bg-red-800 text-white p-3 mb-4 rounded">{error()}</div>
      </Show>

      {/* Loading state */}
      <Show when={info.loading || health.loading}>
        <div class="animate-pulse mb-4 flex items-center">
          <div class="h-4 w-4 bg-blue-500 rounded-full mr-2" />
          <p class="text-blue-400">Loading API information...</p>
        </div>
      </Show>

      {/* API Info */}
      <Show when={info() && !info.error}>
        <div class="bg-gray-700 p-3 rounded mb-4">
          <h3 class="text-lg font-semibold text-white mb-2">API Information</h3>
          <p class="text-gray-200 mb-1">
            <span class="text-gray-400">Name:</span> {info()?.name}
          </p>
          <p class="text-gray-200 mb-1">
            <span class="text-gray-400">Version:</span> {info()?.version}
          </p>
          <p class="text-gray-200 mb-1">
            <span class="text-gray-400">Docs:</span>
            <a
              href={info()?.docs_url}
              class="text-blue-400 hover:text-blue-300 ml-1"
              target="_blank"
              rel="noopener noreferrer"
            >
              API Documentation
            </a>
          </p>
          <p class="text-gray-200">
            <span class="text-gray-400">Description:</span>{' '}
            {info()?.description}
          </p>
        </div>
      </Show>

      {/* Health Status */}
      <Show when={health() && !health.error}>
        <div class="bg-gray-700 p-3 rounded mb-4">
          <h3 class="text-lg font-semibold text-white mb-2">Health Status</h3>
          <p class="text-gray-200 mb-1">
            <span class="text-gray-400">Status:</span>
            <span
              class={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                health()?.status === 'ok'
                  ? 'bg-green-500 text-white'
                  : 'bg-red-500 text-white'
              }`}
            >
              {health()?.status}
            </span>
          </p>
          <p class="text-gray-200 mb-1">
            <span class="text-gray-400">Version:</span> {health()?.version}
          </p>
          <p class="text-gray-200">
            <span class="text-gray-400">Timestamp:</span> {health()?.timestamp}
          </p>
        </div>
      </Show>

      {/* API error display */}
      <Show when={Boolean(info.error) || Boolean(health.error)}>
        <div class="bg-red-800 text-white p-3 mb-4 rounded">
          <h3 class="font-semibold mb-1">Error connecting to API</h3>
          <p class="text-sm">
            {info.error instanceof Error
              ? info.error.message
              : health.error instanceof Error
                ? health.error.message
                : 'Unknown error'}
          </p>
        </div>
      </Show>

      {/* Refresh button */}
      <button
        onClick={handleRefresh}
        class="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white font-medium transition-colors"
        disabled={info.loading || health.loading}
        type="button"
      >
        Refresh API Status
      </button>
    </div>
  )
}

export default ApiInfo
