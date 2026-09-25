'use client'

import { useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'

import { browserApi } from '@/lib/api'

import { UNREAD_KEY } from './notification-bell'

/**
 * Marks what's on screen as read once the page has shown it. The page keeps its unread
 * highlights until the next visit so people can still see what's new.
 */
export function MarkNotificationsRead({ upTo }: { upTo: string | null }) {
  const queryClient = useQueryClient()
  useEffect(() => {
    if (!upTo) return
    void browserApi
      .POST('/v1/me/notifications/read', { body: { up_to: upTo } })
      .then(({ data }) => {
        if (data) queryClient.setQueryData(UNREAD_KEY, data.count)
      })
  }, [upTo, queryClient])
  return null
}
