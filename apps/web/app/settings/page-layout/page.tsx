import { Card } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import type { ReactNode } from 'react'

import { ReadmeForm } from '@/components/readme-form'
import { SectionsForm } from '@/components/sections-form'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Profile page settings' }

function Panel({
  title,
  blurb,
  children,
}: {
  title: string
  blurb: ReactNode
  children: ReactNode
}) {
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

export default async function ProfilePageSettings() {
  const me = await requireMe('/settings/page-layout')
  const { data: profile } = await serverApi(await sessionToken()).GET('/v1/me/profile', {
    cache: 'no-store',
  })
  if (!profile) throw new Error('Could not load your profile.')

  return (
    <div className="grid gap-6">
      <Panel
        title="README"
        blurb={
          <>
            Markdown at the top of{' '}
            <Link href={`/u/${me.username}` as Route} className="text-cyan hover:underline">
              your profile
            </Link>
            : what you work on, what you&apos;re learning, how to reach you.
          </>
        }
      >
        <ReadmeForm initial={profile.readme_md} />
      </Panel>
      <Panel title="Sections" blurb="Pick what your profile shows, and in what order.">
        <SectionsForm initial={profile.sections} />
      </Panel>
    </div>
  )
}
