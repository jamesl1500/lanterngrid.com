import { Avatar, Card, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'

import { languageLabels, type Snippet } from '@/lib/snippets'
import { timeAgo } from '@/lib/time'

import { CodeBlock } from './code-block'

type Props = {
  snippet: Snippet
  /** Lines of code to show before "N more lines". */
  maxLines?: number
  showOwner?: boolean
}

/** A snippet in a list, a pin or a post: title, a few lines of code and a link to the rest. */
export async function SnippetCard({ snippet, maxLines = 12, showOwner = false }: Props) {
  const href = `/snippets/${snippet.id}` as Route
  return (
    <Card className="grid grid-cols-1 border-l-4 border-l-violet">
      <div className="grid gap-1 px-4 pt-3">
        <div className="flex items-start justify-between gap-3">
          <Link href={href} className="min-w-0 font-semibold hover:underline">
            {snippet.title}
          </Link>
          <span className="shrink-0 font-mono text-xs text-violet">
            {languageLabels[snippet.language]}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-x-1.5 font-mono text-xs text-ink-3">
          {showOwner ? (
            <>
              <Link
                href={`/u/${snippet.owner.username}` as Route}
                className="flex items-center gap-1.5 hover:text-ink"
              >
                <Avatar
                  name={snippet.owner.display_name}
                  src={snippet.owner.avatar_url}
                  accent={snippet.owner.accent_color as Accent}
                  size="sm"
                  className="size-5 text-[0.55rem]"
                />
                @{snippet.owner.username}
              </Link>
              <span aria-hidden>·</span>
            </>
          ) : null}
          <span>
            {snippet.line_count} {snippet.line_count === 1 ? 'line' : 'lines'}
          </span>
          <span aria-hidden>·</span>
          <time dateTime={snippet.updated_at}>{timeAgo(snippet.updated_at)}</time>
          {snippet.visibility === 'friends' ? (
            <span className="text-lime">· friends only</span>
          ) : null}
        </div>
        {snippet.description ? <p className="text-sm text-ink-2">{snippet.description}</p> : null}
      </div>
      <div className="px-4 pb-4">
        <CodeBlock
          code={snippet.content}
          lang={snippet.language}
          label={snippet.filename ?? undefined}
          maxLines={maxLines}
          moreHref={href}
        />
      </div>
    </Card>
  )
}
