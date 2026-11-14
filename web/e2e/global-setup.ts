import { apiURL, baseURL } from './env'

/** Fail fast, with a useful message, when the app under test is not running. */
export default async function globalSetup(): Promise<void> {
  const targets = [
    { name: 'web app', url: baseURL, hint: 'cd web && pnpm dev' },
    { name: 'API', url: `${apiURL}/v1/health`, hint: 'make run-api (and docker compose up -d)' },
  ]

  for (const target of targets) {
    const ok = await fetch(target.url)
      .then((response) => response.ok)
      .catch(() => false)
    if (!ok) {
      throw new Error(
        `The ${target.name} is not reachable at ${target.url}. Start it first: ${target.hint}`
      )
    }
  }
}
