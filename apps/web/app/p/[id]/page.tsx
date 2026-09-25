import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { cache } from 'react'

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

type Props = { params: Promise<{ id: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPost((await params).id)
  if (!post) return { title: 'Not found' }
  const excerpt = post.body_md.replace(/\s+/g, ' ').slice(0, 160)
  return { title: `${post.author.display_name} on Lantern Grid`, description: excerpt }
}

export default async function PostPage({ params }: Props) {
  const [post, me] = await Promise.all([getPost((await params).id), getMe()])
  if (!post) notFound()
  return (
    <main className="mx-auto grid max-w-2xl grid-cols-1 gap-6 px-4 py-8">
      <PostCard post={post} viewerId={me?.id} afterDelete="/" />
    </main>
  )
}
