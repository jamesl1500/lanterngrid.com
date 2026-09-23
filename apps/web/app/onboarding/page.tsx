import type { Metadata } from 'next'
import { redirect } from 'next/navigation'

import { AuthCard } from '@/components/auth/auth-card'
import { OnboardingForm } from '@/components/onboarding-form'
import { getMe } from '@/lib/session'

export const metadata: Metadata = { title: 'Set up your profile' }

export default async function OnboardingPage({
  searchParams,
}: {
  searchParams: Promise<{ suggested?: string }>
}) {
  const me = await getMe()
  if (!me) redirect('/signin?next=%2Fonboarding')
  if (me.username) redirect(`/u/${me.username}`)
  const { suggested } = await searchParams

  return (
    <AuthCard eyebrow="one more step" title="Claim your username">
      <p className="text-ink-2">
        Pick the name people will find you by. You can change your name and headline any time.
      </p>
      <OnboardingForm suggestedUsername={suggested} displayName={me.display_name} />
    </AuthCard>
  )
}
