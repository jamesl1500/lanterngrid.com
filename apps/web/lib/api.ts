import { createApiClient } from '@lanterngrid/api-client'

/** API client for server components and route handlers, which call FastAPI directly. */
export function serverApi() {
  return createApiClient(process.env.API_URL ?? 'http://localhost:8000')
}

/** API client for the browser, which goes through the same-origin /api proxy. */
export const browserApi = createApiClient('/api')
