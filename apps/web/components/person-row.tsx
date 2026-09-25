import { Avatar, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import type { ReactNode } from 'react'

import type { Person } from '@/lib/people'

/** One person in a list: avatar, name, handle and headline, with optional actions. */
export function PersonRow({ person, children }: { person: Person; children?: ReactNode }) {
  const href = `/u/${person.username}` as Route
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-line py-3 last:border-b-0">
      <Link href={href} className="flex min-w-0 flex-1 items-center gap-3">
        <Avatar
          name={person.display_name}
          src={person.avatar_url}
          accent={person.accent_color as Accent}
          size="md"
        />
        <span className="grid min-w-0">
          <span className="truncate font-semibold hover:underline">{person.display_name}</span>
          <span className="truncate font-mono text-xs text-ink-3">
            @{person.username}
            {person.headline ? <span className="font-sans"> · {person.headline}</span> : null}
          </span>
        </span>
      </Link>
      {children ? <div className="flex shrink-0 gap-2">{children}</div> : null}
    </li>
  )
}
