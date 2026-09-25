'use client'

import { Avatar, Button, cn, type Accent } from '@lanterngrid/ui'
import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query'
import type { Route } from 'next'
import Link from 'next/link'
import { useEffect } from 'react'

import { browserApi } from '@/lib/api'
import { conversationName, others, type Conversation } from '@/lib/messages'
import { realtime } from '@/lib/realtime'
import { timeAgo } from '@/lib/time'

type Page = { items: Conversation[]; next_cursor: string | null }
type Props = { initial: Page; meId: string; activeId?: string }

export const INBOX_KEY = ['conversations', 'inbox'] as const

/** The inbox: conversations with the newest message first, kept live over the socket. */
export function ConversationList({ initial, meId, activeId }: Props) {
  const queryClient = useQueryClient()
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: INBOX_KEY,
    queryFn: async ({ pageParam }): Promise<Page> => {
      const { data } = await browserApi.GET('/v1/conversations', {
        params: { query: pageParam ? { cursor: pageParam } : {} },
      })
      if (!data) throw new Error('Could not load conversations.')
      return data
    },
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
    initialData: { pages: [initial], pageParams: [null] },
    // The server just rendered this, so don't refetch on mount.
    staleTime: 30_000,
  })

  useEffect(
    () =>
      realtime.subscribe((event) => {
        // Someone else reading doesn't change my inbox; everything else can.
        const changesInbox =
          event.type === 'message.created' ||
          event.type === 'conversation.updated' ||
          event.type === 'reconnected' ||
          (event.type === 'conversation.read' && event.user_id === meId)
        if (changesInbox) void queryClient.invalidateQueries({ queryKey: INBOX_KEY })
      }),
    [meId, queryClient],
  )

  const conversations = data.pages.flatMap((page) => page.items)
  if (conversations.length === 0) {
    return (
      <div className="grid place-items-center gap-2 px-6 py-12 text-center">
        <span className="label">no conversations</span>
        <p className="max-w-[36ch] text-ink-2">Message a friend, or start a group with a few.</p>
      </div>
    )
  }

  return (
    <nav aria-label="Conversations">
      <ol>
        {conversations.map((c) => (
          <ConversationRow key={c.id} conversation={c} meId={meId} active={c.id === activeId} />
        ))}
      </ol>
      {hasNextPage ? (
        <div className="flex justify-center p-3">
          <Button
            size="sm"
            variant="ghost"
            disabled={isFetchingNextPage}
            onClick={() => void fetchNextPage()}
          >
            {isFetchingNextPage ? 'Loading…' : 'More'}
          </Button>
        </div>
      ) : null}
    </nav>
  )
}

function ConversationRow({
  conversation: c,
  meId,
  active,
}: {
  conversation: Conversation
  meId: string
  active: boolean
}) {
  const people = others(c, meId)
  const first = people[0]
  const last = c.last_message
  const unread = c.unread_count > 0 && !active
  const preview = last
    ? `${last.sender?.id === meId ? 'You: ' : c.kind === 'group' && last.sender ? `${last.sender.display_name}: ` : ''}${last.body}`
    : c.kind === 'group'
      ? `${c.members.length} people`
      : 'No messages yet'

  return (
    <li className="border-b border-line last:border-b-0">
      <Link
        href={`/messages/${c.id}` as Route}
        aria-current={active ? 'page' : undefined}
        className={cn(
          'flex items-center gap-3 border-l-4 px-3 py-3 hover:bg-sunk',
          active ? 'border-l-magenta bg-magenta-soft/40' : 'border-l-transparent',
        )}
      >
        <span className="relative shrink-0">
          {first ? (
            <Avatar
              name={first.display_name}
              src={first.avatar_url}
              accent={first.accent_color as Accent}
              size="md"
            />
          ) : (
            <Avatar name={conversationName(c, meId)} size="md" />
          )}
          {people.length > 1 ? (
            <span className="absolute -right-1.5 -bottom-1.5 border border-ground bg-surface px-1 font-mono text-[10px] leading-4 text-ink-2">
              +{people.length - 1}
            </span>
          ) : null}
        </span>
        <span className="grid min-w-0 flex-1">
          <span className="flex items-baseline gap-2">
            <span className={cn('truncate', unread ? 'font-bold' : 'font-semibold')}>
              {conversationName(c, meId)}
            </span>
            <time
              dateTime={c.last_message_at}
              suppressHydrationWarning
              className="ml-auto shrink-0 font-mono text-xs text-ink-3"
            >
              {timeAgo(c.last_message_at)}
            </time>
          </span>
          <span className="flex items-center gap-2">
            <span className={cn('truncate text-sm', unread ? 'text-ink' : 'text-ink-3')}>
              {preview}
            </span>
            {unread ? (
              <span className="ml-auto min-w-5 shrink-0 bg-magenta px-1 text-center font-mono text-xs leading-5 font-bold text-[#0c1017]">
                <span className="sr-only">unread: </span>
                {c.unread_count > 99 ? '99+' : c.unread_count}
              </span>
            ) : null}
          </span>
        </span>
      </Link>
    </li>
  )
}
