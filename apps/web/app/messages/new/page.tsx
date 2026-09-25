import type { Metadata } from 'next'
import Link from 'next/link'

import { NewConversationForm } from '@/components/new-conversation-form'
import { serverApi } from '@/lib/api'
import { allFriends } from '@/lib/messages'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'New message' }

export default async function NewConversationPage() {
  const me = await requireMe('/messages/new')
  const friends = await allFriends(serverApi(await sessionToken()), me.username)

  return (
    <section className="min-h-0 overflow-y-auto">
      <div className="flex h-14 items-center gap-3 border-b-2 border-line-strong bg-surface px-4">
        <Link
          href="/messages"
          aria-label="Back to messages"
          className="font-mono text-ink-2 hover:text-ink lg:hidden"
        >
          ←
        </Link>
        <h2 className="text-xl font-bold">New message</h2>
      </div>
      <div className="mx-auto grid max-w-xl gap-4 px-4 py-6">
        {friends.length === 0 ? (
          <p className="py-10 text-center text-ink-2">
            You can message friends once you have some.{' '}
            <Link href="/friends" className="text-magenta hover:underline">
              Find people
            </Link>
          </p>
        ) : (
          <NewConversationForm friends={friends} />
        )}
      </div>
    </section>
  )
}
