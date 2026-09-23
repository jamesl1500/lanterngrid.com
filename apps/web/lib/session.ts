import type { Schemas } from '@lanterngrid/api-client'
import type { Route } from 'next'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { cache } from 'react'

import { serverApi, SESSION_COOKIE } from './api'

export type Me = Schemas['Me']

export async function sessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value
}

/** The signed-in person, or null. Cached for the rest of the request. */
export const getMe = cache(async (): Promise<Me | null> => {
  const token = await sessionToken()
  if (!token) return null
  try {
    const { data } = await serverApi(token).GET('/v1/auth/me', { cache: 'no-store' })
    return data ?? null
  } catch {
    return null
  }
})

/** For pages that need an account with a username. Sends everyone else where they belong. */
export async function requireMe(returnTo: string): Promise<Me & { username: string }> {
  const me = await getMe()
  if (!me) redirect(`/signin?next=${encodeURIComponent(returnTo)}` as Route)
  if (!me.username) redirect('/onboarding')
  return { ...me, username: me.username }
}

/** Which sign-in methods are switched on. */
export const getProviders = cache(async (): Promise<{ github: boolean }> => {
  try {
    const { data } = await serverApi().GET('/v1/auth/providers', { cache: 'no-store' })
    return data ?? { github: false }
  } catch {
    return { github: false }
  }
})
