'use client'

import { cn } from '@lanterngrid/ui'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const items = [
  { href: '/settings/profile', label: 'Profile' },
  { href: '/settings/account', label: 'Account' },
] as const

export function SettingsNav() {
  const pathname = usePathname()
  return (
    <nav className="flex gap-2 font-mono text-sm md:grid md:gap-0 md:border md:border-line">
      {items.map((item) => {
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
