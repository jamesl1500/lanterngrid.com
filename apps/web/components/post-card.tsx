import { Avatar, Card, cn, KindBadge, Tag, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'

import { achievementInfo, postEntities, type Post } from '@/lib/posts'
import { timeAgo } from '@/lib/time'

import { Markdown } from './markdown'
import { PostImages } from './post-images'
import { PostMenu } from './post-menu'
import { ReactionBar } from './reaction-bar'
import { SnippetCard } from './snippet-card'

// The left edge takes the post kind's accent (full class names so Tailwind can see them).
const kindEdge: Record<Post['kind'], string> = {
  update: 'border-l-cyan',
  snippet: 'border-l-violet',
  achievement: 'border-l-amber',
}

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
  const achievement = post.achievement ? achievementInfo[post.achievement.type] : null
  return (
    <Card className={cn('border-l-4', kindEdge[post.kind])}>
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
        {post.achievement && achievement ? (
          <div className="mx-4 mt-3 flex items-center gap-3 border-2 border-amber bg-amber-soft px-4 py-3">
            <span aria-hidden className="text-3xl leading-none">
              {achievement.emoji}
            </span>
            <div className="min-w-0">
              <div className="font-mono text-xs tracking-[0.08em] text-amber uppercase">
                {achievement.label}
              </div>
              <div className="font-display text-lg leading-snug font-semibold break-words">
                {post.achievement.title}
              </div>
            </div>
          </div>
        ) : null}
        {post.body_md ? (
          <div className="px-4 py-3">
            <Markdown source={post.body_md} entities={postEntities(post)} />
          </div>
        ) : null}
        {post.images.length > 0 ? (
          <div className={cn('px-4 pb-3', !post.body_md && 'pt-3')}>
            <PostImages images={post.images} />
          </div>
        ) : null}
        {post.kind === 'snippet' ? (
          <div className={cn('px-4 pb-3', !post.body_md && 'pt-3')}>
            {post.snippet ? (
              <SnippetCard snippet={post.snippet} maxLines={10} />
            ) : (
              <p className="border border-dashed border-line px-4 py-3 text-sm text-ink-3">
                This snippet was deleted or isn&apos;t shared with you.
              </p>
            )}
          </div>
        ) : null}
        {post.tags.length > 0 ? (
          <ul aria-label="Tags" className="flex flex-wrap gap-1.5 px-4 pb-3">
            {post.tags.map((tag) => (
              <li key={tag.slug}>
                <Link href={`/tags/${encodeURIComponent(tag.slug)}` as Route}>
                  <Tag name={tag.slug} className="hover:underline" />
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
        <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-line px-4 py-2">
          <ReactionBar postId={post.id} initial={post.reactions} signedIn={Boolean(viewerId)} />
          <Link
            href={`/p/${post.id}#comments` as Route}
            className="font-mono text-xs text-ink-2 hover:text-ink hover:underline"
          >
            {post.comment_count === 0
              ? 'comment'
              : `${post.comment_count} ${post.comment_count === 1 ? 'comment' : 'comments'}`}
          </Link>
        </footer>
      </article>
    </Card>
  )
}
