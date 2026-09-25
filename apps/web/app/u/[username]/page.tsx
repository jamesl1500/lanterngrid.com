import { accentClasses, Avatar, Button, Card, cn, Tag, type Accent } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { cache } from 'react'

import { FriendActions } from '@/components/friend-actions'
import { PostList } from '@/components/post-list'
import { RepoCard } from '@/components/repo-card'
import { SnippetCard } from '@/components/snippet-card'
import { serverApi } from '@/lib/api'
import { linkKindLabel, shortUrl } from '@/lib/links'
import { getMe, sessionToken } from '@/lib/session'

// Signed in, the API also says how the viewer relates to this person.
const getProfile = cache(async (username: string) => {
  const api = serverApi(await sessionToken())
  const [profile, friends] = await Promise.all([
    api.GET('/v1/users/{username}', { params: { path: { username } }, cache: 'no-store' }),
    api.GET('/v1/users/{username}/friends', {
      params: { path: { username }, query: { limit: 8 } },
      cache: 'no-store',
    }),
  ])
  return profile.data ? { ...profile.data, friends: friends.data?.items ?? [] } : null
})

type Props = {
  params: Promise<{ username: string }>
  searchParams: Promise<{ cursor?: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const profile = await getProfile((await params).username)
  if (!profile) return { title: 'Not found' }
  return {
    title: `${profile.display_name} (@${profile.username})`,
    description: profile.headline ?? `${profile.display_name} on Lantern Grid`,
  }
}

const joined = new Intl.DateTimeFormat('en', { month: 'long', year: 'numeric' })

export default async function ProfilePage({ params, searchParams }: Props) {
  const { username } = await params
  const [profile, { cursor }, me] = await Promise.all([getProfile(username), searchParams, getMe()])
  if (!profile) notFound()
  const api = serverApi(await sessionToken())
  const path = { username: profile.username }
  const [{ data: posts }, { data: pins }] = await Promise.all([
    api.GET('/v1/users/{username}/posts', {
      params: { path, query: { cursor, limit: 20 } },
      cache: 'no-store',
    }),
    // Pins only head the first page.
    cursor
      ? { data: undefined }
      : api.GET('/v1/users/{username}/pins', { params: { path }, cache: 'no-store' }),
  ])
  const pinned = pins?.items ?? []
  const relationship = profile.relationship
  const isMe = relationship?.status === 'self'
  const accent = accentClasses[profile.accent_color as Accent]
  const website = profile.website?.replace(/^https?:\/\//, '').replace(/\/$/, '')

  return (
    <main className="mx-auto grid max-w-4xl grid-cols-1 gap-8 px-4 py-8">
      <Card raised className="overflow-hidden">
        <div
          className={cn(
            'relative h-36 border-b-2 border-line-strong bg-cover bg-center sm:h-44',
            !profile.banner_url && ['bg-grid', accent.soft],
          )}
          style={
            profile.banner_url
              ? { backgroundImage: `url(${JSON.stringify(profile.banner_url)})` }
              : undefined
          }
        >
          <div className={`absolute inset-x-0 bottom-0 h-1.5 ${accent.solid}`} />
        </div>
        <div className="grid gap-4 px-5 pb-6 sm:px-8">
          <div className="relative -mt-14 flex flex-wrap items-end justify-between gap-4">
            <Avatar
              name={profile.display_name}
              src={profile.avatar_url}
              accent={profile.accent_color as Accent}
              size="xl"
              className="shadow-hard"
            />
            {isMe ? (
              <Button asChild variant="secondary" size="sm">
                <Link href="/settings/profile">Edit profile</Link>
              </Button>
            ) : relationship ? (
              <FriendActions username={profile.username} relationship={relationship} />
            ) : (
              <Button asChild variant="accent" size="sm">
                <Link
                  href={`/signin?next=${encodeURIComponent(`/u/${profile.username}`)}` as Route}
                >
                  Sign in to add friend
                </Link>
              </Button>
            )}
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
            <li>
              <Link
                href={`/u/${profile.username}/friends` as Route}
                className="hover:text-ink hover:underline"
              >
                {profile.friend_count} {profile.friend_count === 1 ? 'friend' : 'friends'}
              </Link>
            </li>
            <li>
              <Link
                href={`/u/${profile.username}/snippets` as Route}
                className="hover:text-ink hover:underline"
              >
                snippets
              </Link>
            </li>
            <li>
              <Link
                href={`/u/${profile.username}/repos` as Route}
                className="hover:text-ink hover:underline"
              >
                repos
              </Link>
            </li>
            <li>joined {joined.format(new Date(profile.joined_at))}</li>
          </ul>
          {profile.tags.length > 0 ? (
            <ul aria-label="Stack" className="flex flex-wrap gap-1.5">
              {profile.tags.map((tag) => (
                <li key={tag.slug}>
                  <Tag name={tag.name} accent={profile.accent_color as Accent} />
                </li>
              ))}
            </ul>
          ) : null}
          {profile.links.length > 0 ? (
            <ul aria-label="Links" className="flex flex-wrap gap-2">
              {profile.links.map((link, index) => (
                <li key={index}>
                  <a
                    href={link.url}
                    rel="me nofollow noopener"
                    target="_blank"
                    className="flex items-center border border-line-strong bg-sunk font-mono text-xs transition-colors hover:bg-surface"
                  >
                    <span className={cn('border-r border-line-strong px-2 py-1', accent.text)}>
                      {linkKindLabel[link.kind]}
                    </span>
                    <span className="max-w-[28ch] truncate px-2 py-1 text-ink-2">
                      {shortUrl(link.url)}
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </Card>

      {pinned.length > 0 ? (
        <section className="grid grid-cols-1 gap-4">
          <h2 className="border-b-2 border-line-strong pb-2 text-xl font-bold">Pinned</h2>
          <ul className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {pinned.map((pin) =>
              pin.snippet ? (
                <li key={pin.snippet.id} className="grid grid-cols-1">
                  <SnippetCard snippet={pin.snippet} maxLines={8} />
                </li>
              ) : pin.repo ? (
                <li key={pin.repo.id} className="grid grid-cols-1">
                  <RepoCard repo={pin.repo} />
                </li>
              ) : null,
            )}
          </ul>
        </section>
      ) : null}

      {profile.friends.length > 0 ? (
        <section className="grid gap-4">
          <div className="flex items-end justify-between border-b-2 border-line-strong pb-2">
            <h2 className="text-xl font-bold">Friends</h2>
            <Link
              href={`/u/${profile.username}/friends` as Route}
              className="font-mono text-xs text-ink-2 hover:text-ink"
            >
              see all {profile.friend_count} →
            </Link>
          </div>
          <ul className="grid grid-cols-4 gap-3 sm:grid-cols-8">
            {profile.friends.map((friend) => (
              <li key={friend.id}>
                <Link
                  href={`/u/${friend.username}` as Route}
                  className="grid justify-items-center gap-1.5 text-center"
                  title={friend.display_name}
                >
                  <Avatar
                    name={friend.display_name}
                    src={friend.avatar_url}
                    accent={friend.accent_color as Accent}
                    size="lg"
                  />
                  <span className="w-full truncate font-mono text-xs text-ink-2">
                    @{friend.username}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="grid grid-cols-1 gap-4">
        <h2 className="border-b-2 border-line-strong pb-2 text-xl font-bold">Posts</h2>
        <PostList
          page={posts ?? { items: [], next_cursor: null }}
          viewerId={me?.id}
          olderHref={(next) => `/u/${profile.username}?cursor=${next}`}
          empty={
            <>
              <span className="label">nothing here yet</span>
              <p className="max-w-[40ch] text-ink-2">
                {isMe
                  ? 'Your updates, snippets and wins will show up here.'
                  : `${profile.display_name} hasn't posted anything you can see yet.`}
              </p>
            </>
          }
        />
      </section>
    </main>
  )
}
