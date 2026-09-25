import { Avatar, Card, KindBadge, Tag, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'

import { postEntities, type Post } from '@/lib/posts'
import { timeAgo } from '@/lib/time'

import { Markdown } from './markdown'
import { PostMenu } from './post-menu'

type Props = {
  post: Post
  /** The signed-in person's id, to show edit and delete on their own posts. */
  viewerId?: string
  /** Where to go after deleting (a post page has nothing left to show). */
  afterDelete?: Route
}

export function PostCard({ post, viewerId, afterDelete }: Props) {
  const { author } = post
  const profile = `/u/${author.username}` as Route
  return (
    <Card className="border-l-4 border-l-cyan">
      <article>
        <header className="flex items-start gap-3 px-4 pt-4">
          <Link href={profile} className="shrink-0">
            <Avatar
              name={author.display_name}
              src={author.avatar_url}
              accent={author.accent_color as Accent}
              size="md"
            />
          </Link>
          <div className="min-w-0 flex-1 leading-tight">
            <Link href={profile} className="font-semibold hover:underline">
              {author.display_name}
            </Link>
            <div className="flex flex-wrap gap-x-1.5 font-mono text-xs text-ink-3">
              <span>@{author.username}</span>
              <span aria-hidden>·</span>
              <Link href={`/p/${post.id}` as Route} className="hover:text-ink hover:underline">
                <time dateTime={post.created_at}>{timeAgo(post.created_at)}</time>
              </Link>
              {post.edited_at ? <span>· edited</span> : null}
              {post.visibility === 'friends' ? (
                <span className="text-lime" title="Only friends can see this">
                  · friends only
                </span>
              ) : null}
            </div>
          </div>
          <KindBadge kind={post.kind} />
          {viewerId === author.id ? <PostMenu postId={post.id} afterDelete={afterDelete} /> : null}
        </header>
        <div className="px-4 py-3">
          <Markdown source={post.body_md} entities={postEntities(post)} />
        </div>
        {post.tags.length > 0 ? (
          <ul aria-label="Tags" className="flex flex-wrap gap-1.5 px-4 pb-4">
            {post.tags.map((tag) => (
              <li key={tag.slug}>
                <Link href={`/tags/${encodeURIComponent(tag.slug)}` as Route}>
                  <Tag name={tag.slug} className="hover:underline" />
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
      </article>
    </Card>
  )
}
