import { omit } from 'solid-js'

/**
 * Solid 1 splitProps compatibility helper for third-party packages (e.g. lucide-solid)
 * that have not migrated to Solid 2's `omit` yet.
 *
 * Returns a reactive local object (getters into props) plus the omitted rest.
 */
export function splitProps(
  props: Record<string, unknown>,
  keys: readonly string[]
): [Record<string, unknown>, Record<string, unknown>] {
  const local: Record<string, unknown> = {}
  for (const key of keys) {
    Object.defineProperty(local, key, {
      enumerable: true,
      configurable: true,
      get: () => props[key],
    })
  }
  const rest = omit(props, ...keys) as Record<string, unknown>
  return [local, rest]
}
