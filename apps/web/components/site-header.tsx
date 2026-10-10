import { Avatar, Button, type Accent } from '@lanterngrid/ui'
import Link from 'next/link'

import { serverApi } from '@/lib/api'
import { getMe, sessionToken } from '@/lib/session'

import { SignOutButton } from './account-actions'
import { Logo } from './logo'
import { MessagesLink } from './messages-link'
import { NotificationBell } from './notification-bell'

async function unreadCounts() {
  try {
    const api = serverApi(await sessionToken())
    const [notifications, conversations] = await Promise.all([
      api.GET('/v1/me/notifications/unread-count', { cache: 'no-store' }),
      api.GET('/v1/conversations/unread-count', { cache: 'no-store' }),
    ])
    return {
      notifications: notifications.data?.count ?? 0,
      conversations: conversations.data?.conversations ?? 0,
    }
  } catch {
    return { notifications: 0, conversations: 0 }
  }
}

export async function SiteHeader() {
  const me = await getMe()
  const unread = me?.username ? await unreadCounts() : { notifications: 0, conversations: 0 }
  return (
    <header className="border-b-2 border-line-strong bg-surface">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4 sm:gap-6">
        <Logo />
        <nav className="flex gap-3 font-mono text-sm text-ink-2 sm:gap-5">
          {me?.username ? (
            <>
              {/* The logo goes home too, so phones skip this link to fit. */}
              <Link href="/" className="hidden hover:text-ink sm:inline">
                feed
              </Link>
              <Link href="/explore" className="hover:text-ink">
                explore
              </Link>
              <Link href="/friends" className="hover:text-ink">
                friends
              </Link>
            </>
          ) : (
            <Link href="/explore" className="hover:text-ink">
              explore
            </Link>
          )}
          <Link href="/kit" className="hidden hover:text-ink sm:inline">
            ui kit
          </Link>
        </nav>
        <div className="ml-auto flex items-center gap-1 sm:gap-2">
          {me ? (
            <>
              {me.username ? (
                <>
                  <MessagesLink meId={me.id} initialCount={unread.conversations} />
                  <NotificationBell initialCount={unread.notifications} />
                </>
              ) : null}
              {me.username ? (
                <Link
                  href={`/u/${me.username}`}
                  className="flex items-center gap-2 font-mono text-sm text-ink-2 hover:text-ink"
                >
                  <Avatar
                    name={me.display_name}
                    src={me.avatar_url}
                    accent={me.accent_color as Accent}
                    size="sm"
                  />
                  <span className="hidden sm:inline">@{me.username}</span>
                </Link>
              ) : (
                <Button asChild size="sm" variant="accent">
                  <Link href="/onboarding">Finish setup</Link>
                </Button>
              )}
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link href="/settings/profile">Settings</Link>
              </Button>
              <span className="hidden sm:contents">
                <SignOutButton />
              </span>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/signin">Sign in</Link>
              </Button>
              <Button asChild variant="accent" size="sm">
                <Link href="/signup">Join</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
