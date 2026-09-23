import { accentClasses, Avatar, Button, Card, type Accent } from '@lanterngrid/ui'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { cache } from 'react'

import { serverApi } from '@/lib/api'
import { getMe } from '@/lib/session'

const getProfile = cache(async (username: string) => {
  const { data } = await serverApi().GET('/v1/users/{username}', {
    params: { path: { username } },
    cache: 'no-store',
  })
  return data ?? null
})

type Props = { params: Promise<{ username: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const profile = await getProfile((await params).username)
  if (!profile) return { title: 'Not found' }
  return {
    title: `${profile.display_name} (@${profile.username})`,
    description: profile.headline ?? `${profile.display_name} on Lantern Grid`,
  }
}

const joined = new Intl.DateTimeFormat('en', { month: 'long', year: 'numeric' })

export default async function ProfilePage({ params }: Props) {
  const profile = await getProfile((await params).username)
  if (!profile) notFound()
  const me = await getMe()
  const isMe = me?.username?.toLowerCase() === profile.username.toLowerCase()
  const accent = accentClasses[profile.accent_color as Accent]
  const website = profile.website?.replace(/^https?:\/\//, '').replace(/\/$/, '')

  return (
    <main className="mx-auto grid max-w-4xl gap-8 px-4 py-8">
      <Card raised className="overflow-hidden">
        <div
          className={`bg-grid relative h-36 border-b-2 border-line-strong sm:h-44 ${accent.soft}`}
        >
          <div className={`absolute inset-x-0 bottom-0 h-1.5 ${accent.solid}`} />
        </div>
        <div className="grid gap-4 px-5 pb-6 sm:px-8">
          <div className="relative -mt-14 flex flex-wrap items-end justify-between gap-4">
            <Avatar
              name={profile.display_name}
              accent={profile.accent_color as Accent}
              size="xl"
              className="shadow-hard"
            />
            {isMe ? (
              <Button asChild variant="secondary" size="sm">
                <Link href="/settings/profile">Edit profile</Link>
              </Button>
            ) : null}
          </div>
          <div className="grid gap-1">
            <h1 className="text-3xl font-bold sm:text-4xl">{profile.display_name}</h1>
            <p className="font-mono text-sm text-ink-3">@{profile.username}</p>
          </div>
          {profile.headline ? <p className="text-lg text-ink">{profile.headline}</p> : null}
          {profile.bio ? (
            <p className="max-w-[65ch] whitespace-pre-line text-ink-2">{profile.bio}</p>
          ) : null}
          <ul className="flex flex-wrap gap-x-5 gap-y-1 font-mono text-xs text-ink-3">
            {profile.location ? <li>{profile.location}</li> : null}
            {profile.website && website ? (
              <li>
                <a
                  href={profile.website}
                  rel="me nofollow noopener"
                  target="_blank"
                  className={`${accent.text} underline-offset-2 hover:underline`}
                >
                  {website}
                </a>
              </li>
            ) : null}
            <li>joined {joined.format(new Date(profile.joined_at))}</li>
          </ul>
        </div>
      </Card>

      <section className="grid gap-4">
        <h2 className="border-b-2 border-line-strong pb-2 text-xl font-bold">Posts</h2>
        <Card className="grid place-items-center gap-2 px-6 py-12 text-center">
          <span className="label">nothing here yet</span>
          <p className="max-w-[40ch] text-ink-2">
            {isMe
              ? 'Your updates, snippets and wins will show up here.'
              : `${profile.display_name} hasn't posted anything yet.`}
          </p>
        </Card>
      </section>
    </main>
  )
}
