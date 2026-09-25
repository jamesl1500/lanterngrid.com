'use client'

import { useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useEffect } from 'react'

import { browserApi } from '@/lib/api'
import { realtime } from '@/lib/realtime'

export const UNREAD_CONVERSATIONS_KEY = ['conversations', 'unread-count'] as const

/** Messages in the header, with how many conversations have unread messages, kept live. */
export function MessagesLink({ meId, initialCount }: { meId: string; initialCount: number }) {
  const queryClient = useQueryClient()
  const { data: count = initialCount } = useQuery({
    queryKey: UNREAD_CONVERSATIONS_KEY,
    queryFn: async () => {
      const { data } = await browserApi.GET('/v1/conversations/unread-count')
      return data?.conversations ?? 0
    },
    initialData: initialCount,
  })

  // This link is on every page, so it also keeps the shared socket open.
  useEffect(
    () =>
      realtime.subscribe((event) => {
        const changesCount =
          (event.type === 'message.created' && event.message.sender?.id !== meId) ||
          (event.type === 'conversation.read' && event.user_id === meId) ||
          event.type === 'conversation.updated' ||
          event.type === 'reconnected'
        if (changesCount) void queryClient.invalidateQueries({ queryKey: UNREAD_CONVERSATIONS_KEY })
      }),
    [meId, queryClient],
  )

  const label = count ? `Messages, ${count} unread` : 'Messages'
  return (
    <Link
      href="/messages"
      aria-label={label}
      title={label}
      className="relative flex size-8 items-center justify-center border-2 border-transparent text-ink-2 hover:border-line-strong hover:bg-sunk hover:text-ink"
    >
      <svg viewBox="0 0 16 16" aria-hidden className="size-4" fill="none" stroke="currentColor">
        <path d="M1.75 2.75h12.5v8.5H7l-3.25 2.5v-2.5h-2z" strokeWidth="1.5" />
      </svg>
      {count > 0 ? (
        <span className="absolute -top-1.5 -right-1.5 min-w-4 border border-ground bg-magenta px-0.5 text-center font-mono text-[10px] leading-4 font-bold text-[#0c1017]">
          {count > 99 ? '99+' : count}
        </span>
      ) : null}
    </Link>
  )
}
