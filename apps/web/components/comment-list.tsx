import { Avatar, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'

import type { Comment } from '@/lib/posts'
import { timeAgo } from '@/lib/time'

import { DeleteCommentButton } from './delete-comment-button'
import { Markdown } from './markdown'

type Props = {
  comments: Comment[]
  viewerId?: string
  /** The post's author can delete any comment on it. */
  postAuthorId: string
}

const noTags = new Set<string>()

export function CommentList({ comments, viewerId, postAuthorId }: Props) {
  return (
    <ol className="grid grid-cols-1">
      {comments.map((comment) => {
        const { author } = comment
        const profile = `/u/${author.username}` as Route
        const canDelete = viewerId !== undefined && [author.id, postAuthorId].includes(viewerId)
        return (
          <li
            key={comment.id}
            id={`comment-${comment.id}`}
            className="flex scroll-mt-20 gap-3 border-b border-line py-4 last:border-b-0 target:bg-cyan-soft/40"
          >
            <Link href={profile} className="shrink-0">
              <Avatar
                name={author.display_name}
                src={author.avatar_url}
                accent={author.accent_color as Accent}
                size="sm"
              />
            </Link>
            <div className="grid min-w-0 flex-1 grid-cols-1 gap-1">
              <div className="flex flex-wrap items-baseline gap-x-2 leading-tight">
                <Link href={profile} className="text-sm font-semibold hover:underline">
                  {author.display_name}
                </Link>
                <span className="font-mono text-xs text-ink-3">
                  @{author.username} ·{' '}
                  <a href={`#comment-${comment.id}`} className="hover:text-ink hover:underline">
                    <time dateTime={comment.created_at}>{timeAgo(comment.created_at)}</time>
                  </a>
                </span>
                {canDelete ? (
                  <span className="ml-auto">
                    <DeleteCommentButton commentId={comment.id} />
                  </span>
                ) : null}
              </div>
              <Markdown
                source={comment.body_md}
                entities={{ tags: noTags, mentions: new Set(comment.mentions) }}
              />
            </div>
          </li>
        )
      })}
    </ol>
  )
}
