import { Button } from '@lanterngrid/ui'
import Link from 'next/link'

import { Logo } from './logo'

export function SiteHeader() {
  return (
    <header className="border-b-2 border-line-strong bg-surface">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4">
        <Logo />
        <nav className="hidden gap-5 font-mono text-sm text-ink-2 sm:flex">
          <Link href="/kit" className="hover:text-ink">
            ui kit
          </Link>
        </nav>
        <div className="ml-auto flex gap-2">
          <Button variant="ghost" size="sm" disabled>
            Sign in
          </Button>
          <Button variant="accent" size="sm" disabled>
            Join
          </Button>
        </div>
      </div>
    </header>
  )
}
