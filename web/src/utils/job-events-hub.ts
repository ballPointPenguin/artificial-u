/**
 * Centralized SSE hub for job events.
 * Maintains a single connection and distributes events to subscribers.
 */

import { createSignal, onCleanup } from 'solid-js'
import { createUrl } from '../api/client.js'
import { ENDPOINTS } from '../api/config.js'
import type { JobEvent } from '../api/services/jobs-service.js'
import { jobDebug } from './job-debug.js'

export type JobEventListener = (event: JobEvent) => void

interface JobEventFilter {
  topicId?: number
  lectureId?: number
  courseId?: number
  kinds?: string[]
}

class JobEventHub {
  private eventSource: EventSource | null = null
  private listeners = new Map<symbol, { filter: JobEventFilter; callback: JobEventListener }>()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private isConnecting = false
  private reconnectDelay = 1000 // Start with 1 second
  private maxReconnectDelay = 30000 // Max 30 seconds

  // Don't connect immediately - wait for first subscriber
  // constructor() { }

  private async getAuthToken(): Promise<string | null> {
    // For now, we'll use a simple approach to get the token
    // In a real implementation, you might want to use the auth context
    // or a global auth state
    try {
      // Import the API client to use its token provider
      const { getAuthToken } = await import('../api/client.js')
      return (await getAuthToken?.()) || null
    } catch {
      return null
    }
  }

  private createAuthenticatedEventSource(url: string, token: string | null): EventSource {
    if (token) {
      // Use the token in the URL as a query parameter (less secure but works)
      const separator = url.includes('?') ? '&' : '?'
      const authenticatedUrl = `${url}${separator}access_token=${encodeURIComponent(token)}`
      return new EventSource(authenticatedUrl)
    } else {
      return new EventSource(url)
    }
  }

  private async connect() {
    if (this.isConnecting || this.eventSource?.readyState === EventSource.OPEN) {
      return
    }

    this.isConnecting = true

    // Create a single SSE connection without filters - get ALL events
    const url = createUrl(ENDPOINTS.jobs.stream)
    jobDebug.log('subscription', `JobEventHub connecting to: ${url}`, null)

    // Get auth token for SSE request
    let token: string | null = null
    try {
      token = await this.getAuthToken()
    } catch (error) {
      jobDebug.log('error', 'Failed to get auth token for SSE', error)
    }

    if (!token) {
      this.isConnecting = false
      jobDebug.log(
        'subscription',
        'JobEventHub skipping connection because no auth token is available',
        null
      )
      return
    }

    // Create EventSource with authorization header
    // Note: EventSource doesn't natively support custom headers in all browsers
    // We'll use a workaround by creating a custom request
    this.eventSource = this.createAuthenticatedEventSource(url, token)

    this.eventSource.addEventListener('open', () => {
      this.isConnecting = false
      this.reconnectDelay = 1000 // Reset delay on successful connection
      jobDebug.log('subscription', 'JobEventHub connection opened', null)
    })

    this.eventSource.addEventListener('job', (ev) => {
      try {
        const me = ev as MessageEvent<string>
        const data = JSON.parse(me.data) as JobEvent
        this.distributeEvent(data)
      } catch (err) {
        jobDebug.log('error', 'Failed to parse job event', err)
      }
    })

    this.eventSource.addEventListener('ping', () => {
      // Keepalive - no action needed
    })

    this.eventSource.addEventListener('connected', () => {
      // Initial connection established - no action needed
      jobDebug.log('subscription', 'JobEventHub received connection confirmation', null)
    })

    this.eventSource.addEventListener('error', () => {
      this.isConnecting = false

      if (this.eventSource?.readyState === EventSource.CLOSED) {
        jobDebug.log('error', 'JobEventHub connection closed, scheduling reconnect', null)
        this.scheduleReconnect()
      }
    })
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      void this.connect() // Handle async connect
      // Exponential backoff
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay)
    }, this.reconnectDelay)
  }

  private distributeEvent(event: JobEvent) {
    jobDebug.log('event', `Distributing event: ${event.kind} #${String(event.id)}`, event)

    // Check each listener's filter and call if matches
    for (const [, { filter, callback }] of this.listeners) {
      if (this.matchesFilter(event, filter)) {
        callback(event)
      }
    }
  }

  private matchesFilter(event: JobEvent, filter: JobEventFilter): boolean {
    // Check kind filter
    if (filter.kinds && filter.kinds.length > 0) {
      if (!filter.kinds.includes(event.kind)) {
        return false
      }
    }

    const payload = event.payload as Record<string, unknown> | undefined
    if (!payload) return true // No payload to filter on

    // Check topic_id filter
    if (filter.topicId !== undefined) {
      const eventTopicId =
        (payload.topic_id as number | undefined) ||
        ((payload.partial_attributes as Record<string, unknown> | undefined)?.topic_id as
          | number
          | undefined)

      if (eventTopicId !== filter.topicId) {
        return false
      }
    }

    // Check lecture_id filter
    if (filter.lectureId !== undefined) {
      const eventLectureId = payload.lecture_id as number | undefined
      if (eventLectureId !== filter.lectureId) {
        return false
      }
    }

    // Check course_id filter
    if (filter.courseId !== undefined) {
      const eventCourseId =
        (payload.course_id as number | undefined) ||
        ((payload.partial_attributes as Record<string, unknown> | undefined)?.course_id as
          | number
          | undefined)

      if (eventCourseId !== filter.courseId) {
        return false
      }
    }

    return true
  }

  subscribe(filter: JobEventFilter, callback: JobEventListener): () => void {
    const id = Symbol('listener')
    this.listeners.set(id, { filter, callback })

    jobDebug.log('subscription', 'Added listener', {
      filter,
      totalListeners: this.listeners.size,
    })

    // Ensure connection is active
    if (!this.eventSource || this.eventSource.readyState === EventSource.CLOSED) {
      void this.connect() // Use void to handle async call
    }

    // Return unsubscribe function
    return () => {
      this.listeners.delete(id)
      jobDebug.log('subscription', 'Removed listener', {
        totalListeners: this.listeners.size,
      })

      if (this.listeners.size === 0) {
        this.disconnect()
      }
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
      jobDebug.log('subscription', 'JobEventHub disconnected', null)
    }
  }
}

// Create singleton instance
let hubInstance: JobEventHub | null = null

export function getJobEventHub(): JobEventHub {
  if (!hubInstance) {
    hubInstance = new JobEventHub()
  }
  return hubInstance
}

// Helper hook for SolidJS components
export function createJobEventSubscription(
  filter: () => JobEventFilter,
  onEvent: JobEventListener
) {
  const [isSubscribed, setIsSubscribed] = createSignal(false)
  let unsubscribe: (() => void) | null = null

  // Subscribe on mount
  const hub = getJobEventHub()
  const currentFilter = filter()

  // Only subscribe if we have valid IDs to filter on
  if (currentFilter.topicId || currentFilter.lectureId || currentFilter.courseId) {
    unsubscribe = hub.subscribe(currentFilter, onEvent)
    setIsSubscribed(true)
  }

  // Cleanup on unmount
  onCleanup(() => {
    if (unsubscribe) {
      unsubscribe()
    }
  })

  return isSubscribed
}
