import type { Metadata } from 'next'
import Link from 'next/link'
import { redirect } from 'next/navigation'

import { AuthCard, OrDivider } from '@/components/auth/auth-card'
import { GitHubButton } from '@/components/auth/github-button'
import { SignUpForm } from '@/components/auth/sign-up-form'
import { homeFor } from '@/lib/routes'
import { getMe, getProviders } from '@/lib/session'

export const metadata: Metadata = { title: 'Create an account' }

export default async function SignUpPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>
}) {
  const { next } = await searchParams
  const me = await getMe()
  if (me) redirect(homeFor(me, next))
  const { github } = await getProviders()

  return (
    <AuthCard
      eyebrow="join lantern grid"
      title="Create your account"
      footer={
        <>
          Already have an account?{' '}
          <Link href="/signin" className="text-cyan underline-offset-2 hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      {github ? (
        <>
          <GitHubButton next={next} label="Sign up with GitHub" />
          <OrDivider />
        </>
      ) : null}
      <SignUpForm />
    </AuthCard>
  )
}
