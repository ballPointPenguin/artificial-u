/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* biome-ignore-all lint/suspicious/noExplicitAny: Debugging */

/**
 * Debug utilities for job management
 * Only active in development mode
 */

export interface JobDebugEvent {
  timestamp: Date
  type: 'subscription' | 'event' | 'state_change' | 'error'
  message: string
  data?: unknown
}

class JobDebugger {
  private events: JobDebugEvent[] = []
  private maxEvents = 100

  log(type: JobDebugEvent['type'], message: string, data?: unknown) {
    if (!import.meta.env.DEV) return

    const event: JobDebugEvent = {
      timestamp: new Date(),
      type,
      message,
      data,
    }

    this.events.push(event)
    if (this.events.length > this.maxEvents) {
      this.events.shift()
    }

    // Log to console with color coding
    const color = {
      subscription: 'color: blue',
      event: 'color: green',
      state_change: 'color: orange',
      error: 'color: red',
    }[type]

    console.log(`%c[JobDebug] ${message}`, color, data || '')
  }

  getEvents() {
    return [...this.events]
  }

  clear() {
    this.events = []
  }

  summary() {
    const summary = {
      total: this.events.length,
      byType: {} as Record<string, number>,
      recentEvents: this.events.slice(-10),
    }

    for (const event of this.events) {
      summary.byType[event.type] = (summary.byType[event.type] || 0) + 1
    }

    return summary
  }
}

// Create a global instance for debugging
export const jobDebug = new JobDebugger()

// Expose to window for console debugging in dev mode
if (import.meta.env.DEV) {
  ;(window as any).jobDebug = jobDebug
}
