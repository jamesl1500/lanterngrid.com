import { Avatar, Button, type Accent } from '@lanterngrid/ui'
import Link from 'next/link'

import { getMe } from '@/lib/session'

import { SignOutButton } from './account-actions'
import { Logo } from './logo'

export async function SiteHeader() {
  const me = await getMe()
  return (
    <header className="border-b-2 border-line-strong bg-surface">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4">
        <Logo />
        <nav className="hidden gap-5 font-mono text-sm text-ink-2 sm:flex">
          <Link href="/kit" className="hover:text-ink">
            ui kit
          </Link>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          {me ? (
            <>
              {me.username ? (
                <Link
                  href={`/u/${me.username}`}
                  className="flex items-center gap-2 font-mono text-sm text-ink-2 hover:text-ink"
                >
                  <Avatar name={me.display_name} accent={me.accent_color as Accent} size="sm" />
                  <span className="hidden sm:inline">@{me.username}</span>
                </Link>
              ) : (
                <Button asChild size="sm" variant="accent">
                  <Link href="/onboarding">Finish setup</Link>
                </Button>
              )}
              <Button asChild variant="ghost" size="sm">
                <Link href="/settings/profile">Settings</Link>
              </Button>
              <SignOutButton />
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
