import { Alert } from '@lanterngrid/ui'
import type { Metadata } from 'next'
import Link from 'next/link'
import { redirect } from 'next/navigation'

import { AuthCard, OrDivider } from '@/components/auth/auth-card'
import { GitHubButton } from '@/components/auth/github-button'
import { SignInForm } from '@/components/auth/sign-in-form'
import { homeFor, safeNext } from '@/lib/routes'
import { getMe, getProviders } from '@/lib/session'

export const metadata: Metadata = { title: 'Sign in' }

const errorMessages: Record<string, string> = {
  github_state: 'GitHub sign-in was interrupted or took too long. Try again.',
  github_failed: "GitHub didn't let us read your profile. Try again.",
  github_email: 'Your GitHub account needs a verified primary email address to sign in.',
}

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>
}) {
  const { next, error } = await searchParams
  const me = await getMe()
  if (me) redirect(homeFor(me, next))
  const { github } = await getProviders()
  const signUpHref = safeNext(next) ? `/signup?next=${encodeURIComponent(next!)}` : '/signup'

  return (
    <AuthCard
      eyebrow="welcome back"
      title="Sign in"
      footer={
        <>
          New here?{' '}
          <Link
            href={signUpHref as '/signup'}
            className="text-cyan underline-offset-2 hover:underline"
          >
            Create an account
          </Link>
        </>
      }
    >
      {error && errorMessages[error] ? <Alert tone="error">{errorMessages[error]}</Alert> : null}
      {github ? (
        <>
          <GitHubButton next={next} />
          <OrDivider />
        </>
      ) : null}
      <SignInForm next={next} />
    </AuthCard>
  )
}
