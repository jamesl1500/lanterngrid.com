'use client'

import { useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useEffect } from 'react'

import { browserApi } from '@/lib/api'
import { realtime } from '@/lib/realtime'

export const UNREAD_KEY = ['notifications', 'unread-count'] as const

/** Bell in the header with the unread count, kept live over the socket. */
export function NotificationBell({ initialCount }: { initialCount: number }) {
  const queryClient = useQueryClient()
  const { data: count = initialCount } = useQuery({
    queryKey: UNREAD_KEY,
    queryFn: async () => {
      const { data } = await browserApi.GET('/v1/me/notifications/unread-count')
      return data?.count ?? 0
    },
    initialData: initialCount,
  })

  useEffect(
    () =>
      realtime.subscribe((event) => {
        const changesCount =
          event.type === 'notification.created' ||
          event.type === 'notifications.read' ||
          event.type === 'reconnected'
        if (changesCount) void queryClient.invalidateQueries({ queryKey: UNREAD_KEY })
      }),
    [queryClient],
  )
  const label = count ? `Notifications, ${count} unread` : 'Notifications'

  return (
    <Link
      href="/notifications"
      aria-label={label}
      title={label}
      className="relative flex size-8 items-center justify-center border-2 border-transparent text-ink-2 hover:border-line-strong hover:bg-sunk hover:text-ink"
    >
      <svg viewBox="0 0 16 16" aria-hidden className="size-4" fill="none" stroke="currentColor">
        <path d="M3 12V7a5 5 0 0 1 10 0v5l1.5 1.5h-13z" strokeWidth="1.5" strokeLinejoin="miter" />
        <path d="M6.5 14.5h3" strokeWidth="1.5" />
      </svg>
      {count > 0 ? (
        <span className="absolute -top-1.5 -right-1.5 min-w-4 border border-ground bg-coral px-0.5 text-center font-mono text-[10px] leading-4 font-bold text-[#0c1017]">
          {count > 99 ? '99+' : count}
        </span>
      ) : null}
    </Link>
  )
}
