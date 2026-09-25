import { Button, Card } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import type { ReactNode } from 'react'

import type { PostPage } from '@/lib/posts'

import { PostCard } from './post-card'

type Props = {
  page: PostPage
  viewerId?: string
  /** Builds the link to the next (older) page from its cursor. */
  olderHref: (cursor: string) => string
  empty: ReactNode
}

/** A page of posts with a link to older ones. */
export function PostList({ page, viewerId, olderHref, empty }: Props) {
  if (page.items.length === 0) {
    return <Card className="grid place-items-center gap-2 px-6 py-12 text-center">{empty}</Card>
  }
  return (
    <div className="grid grid-cols-1 gap-4">
      <ol className="grid grid-cols-1 gap-4">
        {page.items.map((post) => (
          <li key={post.id}>
            <PostCard post={post} viewerId={viewerId} />
          </li>
        ))}
      </ol>
      {page.next_cursor ? (
        <Button asChild variant="secondary" className="justify-self-center">
          <Link href={olderHref(page.next_cursor) as Route}>Older posts</Link>
        </Button>
      ) : null}
    </div>
  )
}
