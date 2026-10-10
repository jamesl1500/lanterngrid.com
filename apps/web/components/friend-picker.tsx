'use client'

import { Avatar, Input, cn, type Accent } from '@lanterngrid/ui'
import { useState } from 'react'

import type { Person } from '@/lib/people'

type Props = {
  friends: Person[]
  selected: string[]
  onChange: (usernames: string[]) => void
  /** Most people that can be picked. */
  max: number
}

/** Tick friends to message, with a filter box for long lists. */
export function FriendPicker({ friends, selected, onChange, max }: Props) {
  const [filter, setFilter] = useState('')
  const needle = filter.trim().toLowerCase().replace(/^@/, '')
  const shown = needle
    ? friends.filter(
        (f) =>
          f.username.toLowerCase().includes(needle) ||
          f.display_name.toLowerCase().includes(needle),
      )
    : friends
  const full = selected.length >= max

  function toggle(username: string) {
    onChange(
      selected.includes(username)
        ? selected.filter((u) => u !== username)
        : full
          ? selected
          : [...selected, username],
    )
  }

  return (
    <div className="grid gap-2">
      <label htmlFor="friend-filter" className="sr-only">
        Filter friends
      </label>
      <Input
        id="friend-filter"
        type="search"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter friends"
        autoComplete="off"
      />
      <ul className="max-h-80 overflow-y-auto border-2 border-line-strong bg-surface">
        {shown.length === 0 ? (
          <li className="px-4 py-6 text-center text-ink-3">No friends match.</li>
        ) : (
          shown.map((f) => {
            const checked = selected.includes(f.username)
            return (
              <li key={f.id} className="border-b border-line last:border-b-0">
                <label
                  className={cn(
                    'flex cursor-pointer items-center gap-3 border-l-4 px-3 py-2 hover:bg-sunk',
                    checked ? 'border-l-magenta bg-magenta-soft/40' : 'border-l-transparent',
                    !checked && full && 'cursor-not-allowed opacity-50',
                  )}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={!checked && full}
                    onChange={() => toggle(f.username)}
                    className="size-4 accent-magenta"
                  />
                  <Avatar
                    name={f.display_name}
                    src={f.avatar_url}
                    accent={f.accent_color as Accent}
                    size="sm"
                  />
                  <span className="grid min-w-0">
                    <span className="truncate font-semibold">{f.display_name}</span>
                    <span className="truncate font-mono text-xs text-ink-3">@{f.username}</span>
                  </span>
                </label>
              </li>
            )
          })
        )}
      </ul>
    </div>
  )
}
