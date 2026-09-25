import { Button, Card, KindBadge, type ContentKind } from '@lanterngrid/ui'
import Link from 'next/link'
import { Suspense } from 'react'

import { ApiStatus } from '@/components/api-status'
import { GitHubMark } from '@/components/auth/github-button'
import { SamplePost } from '@/components/sample-post'
import { githubStartUrl } from '@/lib/routes'
import { getMe, getProviders } from '@/lib/session'

import { Feed } from './feed'

const features: { kind: ContentKind; title: string; body: string }[] = [
  {
    kind: 'update',
    title: 'Posts',
    body: 'Share what you shipped, what broke and what you learned, in Markdown.',
  },
  {
    kind: 'snippet',
    title: 'Snippets',
    body: 'Highlighted, copyable code you can drop into any post or chat.',
  },
  {
    kind: 'repo',
    title: 'Repos',
    body: 'Share a GitHub repo as a live card with stars, language and topics.',
  },
  {
    kind: 'achievement',
    title: 'Achievements',
    body: 'Promotions, launches, first merged PR. Celebrate the wins.',
  },
  {
    kind: 'message',
    title: 'Messages',
    body: 'Realtime DMs and small groups with the engineers you know.',
  },
]

async function HeroActions() {
  const me = await getMe()
  if (me) {
    return (
      <div className="flex flex-wrap gap-3">
        <Button asChild variant="accent" size="lg">
          <Link href={me.username ? `/u/${me.username}` : '/onboarding'}>
            {me.username ? 'View your profile' : 'Finish setting up'}
          </Link>
        </Button>
      </div>
    )
  }
  const { github } = await getProviders()
  return (
    <div className="flex flex-wrap gap-3">
      {github ? (
        <Button asChild variant="accent" size="lg">
          <a href={githubStartUrl()}>
            <GitHubMark className="size-4" /> Join with GitHub
          </a>
        </Button>
      ) : null}
      <Button asChild variant={github ? 'secondary' : 'accent'} size="lg">
        <Link href="/signup">{github ? 'Join with email' : 'Create an account'}</Link>
      </Button>
      <Button asChild variant="ghost" size="lg">
        <Link href="/signin">Sign in</Link>
      </Button>
    </div>
  )
}

type Props = { searchParams: Promise<{ cursor?: string }> }

/** Your feed once you have a username; the landing page for everyone else. */
export default async function HomePage({ searchParams }: Props) {
  const me = await getMe()
  if (me?.username) return <Feed me={{ ...me, username: me.username }} {...await searchParams} />
  return <Landing />
}

function Landing() {
  return (
    <main className="mx-auto grid max-w-6xl gap-14 px-4 py-10">
      <section className="grid items-start gap-10 lg:grid-cols-[1.1fr_1fr]">
        <div className="bg-grid grid gap-6 border-2 border-line-strong bg-surface p-7 shadow-hard">
          <span className="label">the social network for software engineers</span>
          <h1 className="text-4xl leading-[1.05] font-bold sm:text-6xl">
            Ship it.
            <br />
            Share it<span className="text-amber">_</span>
          </h1>
          <p className="max-w-[52ch] text-lg text-ink-2">
            Post updates, drop code snippets, show off your repos and celebrate your wins with
            engineers who get it.
          </p>
          <HeroActions />
          <div aria-hidden className="flex h-1.5">
            <i className="flex-1 bg-cyan" />
            <i className="flex-1 bg-lime" />
            <i className="flex-1 bg-amber" />
            <i className="flex-1 bg-violet" />
            <i className="flex-1 bg-magenta" />
            <i className="flex-1 bg-coral" />
          </div>
        </div>
        <SamplePost />
      </section>

      <section className="grid gap-5">
        <h2 className="border-b-2 border-line-strong pb-2 text-2xl font-bold">
          What you can share
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {features.map((f) => (
            <Card key={f.kind} className="grid content-start gap-2 p-4">
              <KindBadge kind={f.kind} className="justify-self-start" />
              <h3 className="text-lg font-semibold">{f.title}</h3>
              <p className="text-sm text-ink-2">{f.body}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid max-w-md gap-3">
        <Suspense fallback={<Card className="h-40 animate-pulse" />}>
          <ApiStatus />
        </Suspense>
      </section>
    </main>
  )
}
