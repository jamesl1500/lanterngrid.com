'use client'

import { cn } from '@lanterngrid/ui'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const items = [
  { href: '/settings/profile', label: 'Profile' },
  { href: '/settings/page-layout', label: 'Profile page' },
  { href: '/settings/account', label: 'Account' },
  { href: '/settings/blocked', label: 'Blocked' },
] as const

/** `moderator` adds a link to the report queue. */
export function SettingsNav({ moderator }: { moderator: boolean }) {
  const pathname = usePathname()
  const shown = moderator ? [...items, { href: '/mod', label: 'Moderation' } as const] : items
  return (
    <nav className="flex flex-wrap gap-2 font-mono text-sm md:grid md:gap-0 md:border md:border-line">
      {shown.map((item) => {
        const active = pathname === item.href
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? 'page' : undefined}
            className={cn(
              'border border-line px-3 py-2 md:border-0 md:border-l-4 md:border-l-transparent',
              active
                ? 'bg-surface text-ink md:border-l-cyan'
                : 'text-ink-2 hover:bg-sunk hover:text-ink',
            )}
          >
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}
