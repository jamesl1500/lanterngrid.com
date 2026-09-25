import { Card, type Accent } from '@lanterngrid/ui'
import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { ImageUploader } from '@/components/image-uploader'
import { LinksForm } from '@/components/links-form'
import { ProfileForm } from '@/components/profile-form'
import { TagsForm } from '@/components/tags-form'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Profile settings' }

function Panel({ title, blurb, children }: { title: string; blurb: string; children: ReactNode }) {
  return (
    <Card className="grid gap-6 p-6">
      <header className="grid gap-1">
        <h2 className="text-xl font-bold">{title}</h2>
        <p className="text-sm text-ink-2">{blurb}</p>
      </header>
      {children}
    </Card>
  )
}

export default async function ProfileSettingsPage() {
  await requireMe('/settings/profile')
  const { data: profile } = await serverApi(await sessionToken()).GET('/v1/me/profile', {
    cache: 'no-store',
  })
  if (!profile) throw new Error('Could not load your profile.')
  const accent = profile.accent_color as Accent

  return (
    <div className="grid gap-6">
      <Panel title="Profile" blurb="This is what everyone sees on your profile page.">
        <ProfileForm profile={profile} />
      </Panel>
      <Panel title="Pictures" blurb="Your avatar shows next to everything you post.">
        <div className="grid gap-8">
          <ImageUploader
            kind="avatar"
            url={profile.avatar_url}
            name={profile.display_name}
            accent={accent}
          />
          <ImageUploader
            kind="banner"
            url={profile.banner_url}
            name={profile.display_name}
            accent={accent}
          />
        </div>
      </Panel>
      <Panel title="Stack" blurb="Tags help people with the same interests find you.">
        <TagsForm tags={profile.tags} accent={accent} />
      </Panel>
      <Panel title="Links" blurb="Shown on your profile in this order.">
        <LinksForm links={profile.links} />
      </Panel>
    </div>
  )
}
