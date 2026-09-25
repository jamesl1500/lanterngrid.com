import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { SnippetForm } from '@/components/snippet-form'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Edit snippet' }

type Props = { params: Promise<{ id: string }> }

export default async function EditSnippetPage({ params }: Props) {
  const { id } = await params
  const me = await requireMe(`/snippets/${id}/edit`)
  const { data: snippet } = await serverApi(await sessionToken()).GET('/v1/snippets/{snippet_id}', {
    params: { path: { snippet_id: id } },
    cache: 'no-store',
  })
  // Only the owner can edit; everyone else gets the same 404 as a missing snippet.
  if (!snippet || snippet.owner.id !== me.id) notFound()

  return (
    <main className="mx-auto grid max-w-3xl grid-cols-1 gap-6 px-4 py-8">
      <h1 className="text-3xl font-bold">Edit snippet</h1>
      <SnippetForm editing={snippet} />
    </main>
  )
}
