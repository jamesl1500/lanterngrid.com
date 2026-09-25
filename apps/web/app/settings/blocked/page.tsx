import { Card } from '@lanterngrid/ui'
import type { Metadata } from 'next'

import { PersonRow } from '@/components/person-row'
import { UnblockButton } from '@/components/unblock-button'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Blocked people' }

export default async function BlockedPage() {
  await requireMe('/settings/blocked')
  const { data: blocked } = await serverApi(await sessionToken()).GET('/v1/me/blocks', {
    cache: 'no-store',
  })
  if (!blocked) throw new Error('Could not load blocked people.')

  return (
    <Card className="grid gap-4 p-6">
      <header className="grid gap-1">
        <h2 className="text-xl font-bold">Blocked people</h2>
        <p className="text-sm text-ink-2">
          They can&apos;t see your profile, find you in search or send you requests. They
          aren&apos;t told. Unblocking doesn&apos;t make you friends again.
        </p>
      </header>
      {blocked.length ? (
        <ul>
          {blocked.map((person) => (
            <PersonRow key={person.id} person={person}>
              <UnblockButton username={person.username} />
            </PersonRow>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-ink-3">You haven&apos;t blocked anyone.</p>
      )}
    </Card>
  )
}
