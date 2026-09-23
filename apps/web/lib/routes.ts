import type { Route } from 'next'

/** Only same-site paths, so a `next` parameter can't send people to another site. */
export function safeNext(next: string | null | undefined): Route | null {
  if (next && next.startsWith('/') && !next.startsWith('//') && !next.includes('\\')) {
    return next as Route
  }
  return null
}

/** Where to go after signing in: onboarding if unfinished, else where they came from. */
export function homeFor(me: { username: string | null }, next?: string | null): Route {
  if (!me.username) return '/onboarding'
  return safeNext(next) ?? (`/u/${me.username}` as Route)
}

export function githubStartUrl(next?: string | null): string {
  const target = safeNext(next)
  return `/api/v1/auth/github/start${target ? `?next=${encodeURIComponent(target)}` : ''}`
}
