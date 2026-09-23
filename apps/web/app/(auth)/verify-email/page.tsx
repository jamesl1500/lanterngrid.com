import { Alert, Button } from '@lanterngrid/ui'
import type { Metadata } from 'next'
import Link from 'next/link'

import { AuthCard } from '@/components/auth/auth-card'
import { serverApi } from '@/lib/api'
import { homeFor } from '@/lib/routes'
import { getMe } from '@/lib/session'

export const metadata: Metadata = { title: 'Verify your email' }

export default async function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>
}) {
  const { token } = await searchParams
  let verified = false
  if (token) {
    try {
      const { response } = await serverApi().POST('/v1/auth/verify-email', { body: { token } })
      verified = response.ok
    } catch {
      verified = false
    }
  }
  const me = await getMe()

  return (
    <AuthCard eyebrow="email" title={verified ? 'Email verified' : "That link didn't work"}>
      {verified ? (
        <Alert tone="success">Thanks. Your email address is confirmed.</Alert>
      ) : (
        <Alert tone="error">
          The link has expired or was already used. Sign in and send a new one from your account
          settings.
        </Alert>
      )}
      <Button asChild size="lg">
        <Link href={me ? homeFor(me) : '/signin'}>{me ? 'Continue' : 'Sign in'}</Link>
      </Button>
    </AuthCard>
  )
}
