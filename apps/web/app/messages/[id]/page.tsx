import { Avatar, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { ChatView } from '@/components/chat-view'
import { ConversationActions } from '@/components/conversation-actions'
import { serverApi } from '@/lib/api'
import { allFriends, conversationName, others } from '@/lib/messages'
import { requireMe, sessionToken } from '@/lib/session'

export default async function ConversationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const me = await requireMe(`/messages/${id}`)
  const api = serverApi(await sessionToken())
  const path = { params: { path: { conversation_id: id } }, cache: 'no-store' as const }

  const [conversation, messages] = await Promise.all([
    api.GET('/v1/conversations/{conversation_id}', path),
    api.GET('/v1/conversations/{conversation_id}/messages', path),
  ])
  if (conversation.response.status === 404 || conversation.response.status === 422) notFound()
  if (!conversation.data || !messages.data) throw new Error('Could not load the conversation.')
  const c = conversation.data

  const group = c.kind === 'group'
  const people = others(c, me.id)
  const owner = c.members.some((m) => m.user.id === me.id && m.role === 'owner')
  // Owners can add friends who aren't in the group yet.
  const memberIds = new Set(c.members.map((m) => m.user.id))
  const addable =
    group && owner ? (await allFriends(api, me.username)).filter((f) => !memberIds.has(f.id)) : null
  const peer = !group ? people[0] : undefined

  return (
    <section className="flex min-h-0 flex-col bg-ground">
      <header className="relative flex h-14 shrink-0 items-center gap-3 border-b-2 border-line-strong bg-surface px-4">
        <Link
          href="/messages"
          aria-label="Back to messages"
          className="font-mono text-ink-2 hover:text-ink lg:hidden"
        >
          ←
        </Link>
        <div className="flex shrink-0 -space-x-2">
          {people.slice(0, 3).map((p) => (
            <Avatar
              key={p.id}
              name={p.display_name}
              src={p.avatar_url}
              accent={p.accent_color as Accent}
              size="sm"
              className="ring-2 ring-surface"
            />
          ))}
        </div>
        <div className="grid min-w-0 flex-1">
          <h2 className="truncate text-lg leading-tight font-bold">{conversationName(c, me.id)}</h2>
          {peer ? (
            <Link
              href={`/u/${peer.username}` as Route}
              className="truncate font-mono text-xs text-ink-3 hover:text-ink hover:underline"
            >
              @{peer.username}
            </Link>
          ) : (
            <span className="truncate font-mono text-xs text-ink-3">
              {c.members.length} people
              {c.title ? ` · ${people.map((p) => p.display_name).join(', ')}` : ''}
            </span>
          )}
        </div>
        {group ? (
          <ConversationActions
            conversationId={c.id}
            memberCount={c.members.length}
            addable={addable}
          />
        ) : null}
      </header>
      <ChatView
        key={c.id}
        conversation={c}
        messages={messages.data.items}
        olderCursor={messages.data.older_cursor}
        me={me}
      />
    </section>
  )
}
