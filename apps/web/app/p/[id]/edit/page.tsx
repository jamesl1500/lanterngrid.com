import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { Composer } from '@/components/composer'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Edit post' }

type Props = { params: Promise<{ id: string }> }

export default async function EditPostPage({ params }: Props) {
  const { id } = await params
  const me = await requireMe(`/p/${id}/edit`)
  const { data: post } = await serverApi(await sessionToken()).GET('/v1/posts/{post_id}', {
    params: { path: { post_id: id } },
    cache: 'no-store',
  })
  // Only the author can edit; everyone else gets the same 404 as a missing post.
  if (!post || post.author.id !== me.id) notFound()

  return (
    <main className="mx-auto grid max-w-2xl grid-cols-1 gap-6 px-4 py-8">
      <h1 className="text-3xl font-bold">Edit post</h1>
      <Composer
        me={me}
        editing={{ id: post.id, body_md: post.body_md, visibility: post.visibility }}
      />
    </main>
  )
}
