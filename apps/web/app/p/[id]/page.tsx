import { Button, Card } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { cache } from 'react'

import { CommentForm } from '@/components/comment-form'
import { CommentList } from '@/components/comment-list'
import { PostCard } from '@/components/post-card'
import { serverApi } from '@/lib/api'
import { getMe, sessionToken } from '@/lib/session'

const getPost = cache(async (id: string) => {
  const { data } = await serverApi(await sessionToken()).GET('/v1/posts/{post_id}', {
    params: { path: { post_id: id } },
    cache: 'no-store',
  })
  return data ?? null
})

type Props = {
  params: Promise<{ id: string }>
  searchParams: Promise<{ after?: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPost((await params).id)
  if (!post) return { title: 'Not found' }
  const excerpt = post.body_md.replace(/\s+/g, ' ').slice(0, 160)
  return { title: `${post.author.display_name} on Lantern Grid`, description: excerpt }
}

export default async function PostPage({ params, searchParams }: Props) {
  const { id } = await params
  const [post, me, { after }] = await Promise.all([getPost(id), getMe(), searchParams])
  if (!post) notFound()
  const { data: comments } = await serverApi(await sessionToken()).GET(
    '/v1/posts/{post_id}/comments',
    {
      params: { path: { post_id: post.id }, query: { cursor: after, limit: 50 } },
      cache: 'no-store',
    },
  )
  const items = comments?.items ?? []

  return (
    <main className="mx-auto grid max-w-2xl grid-cols-1 gap-6 px-4 py-8">
      <PostCard post={post} viewerId={me?.id} afterDelete="/" />
      <section id="comments" aria-labelledby="comments-title" className="grid scroll-mt-20 gap-4">
        <h2 id="comments-title" className="border-b-2 border-line-strong pb-2 text-xl font-bold">
          Comments{post.comment_count > 0 ? ` (${post.comment_count})` : ''}
        </h2>
        {after ? (
          <Link
            href={`/p/${post.id}#comments` as Route}
            className="font-mono text-xs text-ink-2 hover:text-ink"
          >
            ← first comments
          </Link>
        ) : null}
        {items.length > 0 ? (
          <Card className="px-4">
            <CommentList comments={items} viewerId={me?.id} postAuthorId={post.author.id} />
          </Card>
        ) : after ? null : (
          <p className="text-ink-2">No comments yet.</p>
        )}
        {comments?.next_cursor ? (
          <Button asChild variant="secondary" className="justify-self-center">
            <Link href={`/p/${post.id}?after=${comments.next_cursor}#comments` as Route}>
              More comments
            </Link>
          </Button>
        ) : me?.username ? (
          <CommentForm postId={post.id} />
        ) : (
          <p className="text-ink-2">
            <Link
              href={`/signin?next=${encodeURIComponent(`/p/${post.id}`)}` as Route}
              className="text-cyan hover:underline"
            >
              Sign in
            </Link>{' '}
            to join the conversation.
          </p>
        )}
      </section>
    </main>
  )
}
