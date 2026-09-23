import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

export type { components, paths }
export type Schemas = components['schemas']

/**
 * Typed client for the Lantern Grid API. Paths, params and response bodies all come from
 * the API's OpenAPI schema, so a backend change that breaks a caller fails typecheck.
 *
 * In the browser, pass `/api` (Next.js proxies it to FastAPI on the same origin).
 * On the server, pass the API's own URL.
 */
export function createApiClient(baseUrl: string, init?: { headers?: HeadersInit }) {
  return createClient<paths>({ baseUrl, headers: init?.headers })
}

export type ApiClient = ReturnType<typeof createApiClient>
