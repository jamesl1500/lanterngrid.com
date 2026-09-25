import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { InboxPane } from '@/components/inbox-pane'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Messages' }

/** The inbox beside whatever is open. Phones show one or the other. */
export default async function MessagesLayout({ children }: { children: ReactNode }) {
  const me = await requireMe('/messages')
  const { data } = await serverApi(await sessionToken()).GET('/v1/conversations', {
    cache: 'no-store',
  })
  if (!data) throw new Error('Could not load conversations.')

  return (
    // Fill the screen under the header, so the chat scrolls and the composer stays put.
    <div
      data-fill-screen
      className="mx-auto grid min-h-0 w-full max-w-6xl flex-1 border-line-strong lg:grid-cols-[22rem_1fr] lg:border-x-2"
    >
      <InboxPane initial={data} meId={me.id} />
      {children}
    </div>
  )
}
