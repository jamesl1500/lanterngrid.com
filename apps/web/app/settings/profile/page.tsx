import { Card } from '@lanterngrid/ui'
import type { Metadata } from 'next'

import { ProfileForm } from '@/components/profile-form'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Profile settings' }

export default async function ProfileSettingsPage() {
  await requireMe('/settings/profile')
  const { data: profile } = await serverApi(await sessionToken()).GET('/v1/me/profile', {
    cache: 'no-store',
  })
  if (!profile) throw new Error('Could not load your profile.')

  return (
    <Card className="grid gap-6 p-6">
      <header className="grid gap-1">
        <h2 className="text-xl font-bold">Profile</h2>
        <p className="text-sm text-ink-2">This is what everyone sees on your profile page.</p>
      </header>
      <ProfileForm profile={profile} />
    </Card>
  )
}
