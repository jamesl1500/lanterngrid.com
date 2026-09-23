import { createApiClient } from '@lanterngrid/api-client'

export const SESSION_COOKIE = 'lg_session'

/**
 * API client for server components, which call FastAPI directly. Pass the session token to
 * act as the signed-in person.
 */
export function serverApi(sessionToken?: string) {
  return createApiClient(process.env.API_URL ?? 'http://localhost:8000', {
    headers: sessionToken ? { cookie: `${SESSION_COOKIE}=${sessionToken}` } : undefined,
  })
}

/** API client for the browser, which goes through the same-origin /api proxy. */
export const browserApi = createApiClient('/api')
