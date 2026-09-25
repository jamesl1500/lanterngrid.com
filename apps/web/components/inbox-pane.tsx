'use client'

import { Button, cn } from '@lanterngrid/ui'
import Link from 'next/link'
import { useSelectedLayoutSegment } from 'next/navigation'
import type { ComponentProps } from 'react'

import { ConversationList } from './conversation-list'

type Props = Omit<ComponentProps<typeof ConversationList>, 'activeId'>

/** The inbox column. On phones it hides while a conversation is open. */
export function InboxPane({ initial, meId }: Props) {
  const segment = useSelectedLayoutSegment()
  const activeId = segment && segment !== 'new' ? segment : undefined
  return (
    <aside
      className={cn(
        'min-h-0 flex-col border-line-strong bg-surface lg:flex lg:border-r-2',
        segment ? 'hidden' : 'flex',
      )}
    >
      <div className="flex h-14 shrink-0 items-center justify-between gap-4 border-b-2 border-line-strong px-4">
        <h1 className="text-xl font-bold">Messages</h1>
        <Button asChild size="sm" className="bg-magenta text-[#0c1017]">
          <Link href="/messages/new">New</Link>
        </Button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <ConversationList initial={initial} meId={meId} activeId={activeId} />
      </div>
    </aside>
  )
}
