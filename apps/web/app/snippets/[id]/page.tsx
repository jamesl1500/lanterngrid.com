import { Avatar, KindBadge, type Accent } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { cache } from 'react'

import { CodeBlock } from '@/components/code-block'
import { SnippetActions } from '@/components/snippet-actions'
import { serverApi } from '@/lib/api'
import { getMe, sessionToken } from '@/lib/session'
import { languageLabels } from '@/lib/snippets'
import { timeAgo } from '@/lib/time'

const getSnippet = cache(async (id: string) => {
  const { data } = await serverApi(await sessionToken()).GET('/v1/snippets/{snippet_id}', {
    params: { path: { snippet_id: id } },
    cache: 'no-store',
  })
  return data ?? null
})

type Props = { params: Promise<{ id: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const snippet = await getSnippet((await params).id)
  if (!snippet) return { title: 'Not found' }
  return {
    title: `${snippet.title} by @${snippet.owner.username}`,
    description: snippet.description || `${languageLabels[snippet.language]} snippet`,
  }
}

export default async function SnippetPage({ params }: Props) {
  const [snippet, me] = await Promise.all([getSnippet((await params).id), getMe()])
  if (!snippet) notFound()
  const { owner } = snippet
  const isOwner = me?.id === owner.id
  let pinned = false
  if (isOwner) {
    const { data } = await serverApi(await sessionToken()).GET('/v1/users/{username}/pins', {
      params: { path: { username: owner.username } },
      cache: 'no-store',
    })
    pinned = data?.items.some((p) => p.snippet?.id === snippet.id) ?? false
  }

  return (
    <main className="mx-auto grid max-w-4xl grid-cols-1 gap-6 px-4 py-8">
      <header className="grid gap-3">
        <div className="flex items-center gap-3">
          <KindBadge kind="snippet" />
          <span className="font-mono text-xs text-violet">{languageLabels[snippet.language]}</span>
          {snippet.visibility === 'friends' ? (
            <span className="font-mono text-xs text-lime">friends only</span>
          ) : null}
        </div>
        <h1 className="text-3xl font-bold break-words">{snippet.title}</h1>
        <Link
          href={`/u/${owner.username}` as Route}
          className="flex items-center gap-2 justify-self-start font-mono text-sm text-ink-2 hover:text-ink"
        >
          <Avatar
            name={owner.display_name}
            src={owner.avatar_url}
            accent={owner.accent_color as Accent}
            size="sm"
          />
          <span>
            {owner.display_name} <span className="text-ink-3">@{owner.username}</span>
          </span>
          <span className="text-ink-3">
            · {snippet.line_count} {snippet.line_count === 1 ? 'line' : 'lines'} · updated{' '}
            <time dateTime={snippet.updated_at}>{timeAgo(snippet.updated_at)}</time>
          </span>
        </Link>
        {snippet.description ? (
          <p className="max-w-[70ch] whitespace-pre-line text-ink-2">{snippet.description}</p>
        ) : null}
      </header>
      {isOwner ? <SnippetActions snippet={snippet} pinned={pinned} /> : null}
      <CodeBlock
        code={snippet.content}
        lang={snippet.language}
        label={snippet.filename ?? undefined}
        lineNumbers
      />
      <Link
        href={`/u/${owner.username}/snippets` as Route}
        className="font-mono text-xs text-ink-2 hover:text-ink"
      >
        ← more snippets from @{owner.username}
      </Link>
    </main>
  )
}
