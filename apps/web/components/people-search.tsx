'use client'

import { Avatar, cn, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import { useRouter } from 'next/navigation'
import { useEffect, useId, useState, type KeyboardEvent } from 'react'

import { searchPeople, type Person } from '@/lib/people'

/** Find people by username or name. Enter opens the highlighted profile. */
export function PeopleSearch({ autoFocus }: { autoFocus?: boolean }) {
  const router = useRouter()
  const id = useId()
  const listId = `${id}-results`
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<{ query: string; people: Person[] } | null>(null)
  const [active, setActive] = useState(0)
  const [open, setOpen] = useState(false)
  const q = query.trim()
  const people = results && results.query === q ? results.people : []
  const showList = open && q !== '' && results?.query === q

  useEffect(() => {
    if (!q) return
    let cancelled = false
    const timer = setTimeout(async () => {
      try {
        const found = await searchPeople(q)
        if (!cancelled) setResults({ query: q, people: found })
      } catch {
        // Keep whatever was showing; the next keystroke tries again.
      }
    }, 200)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [q])

  function go(person: Person | undefined) {
    if (!person) return
    setOpen(false)
    router.push(`/u/${person.username}` as Route)
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown' && people.length) {
      event.preventDefault()
      setActive((i) => (i + 1) % people.length)
    } else if (event.key === 'ArrowUp' && people.length) {
      event.preventDefault()
      setActive((i) => (i - 1 + people.length) % people.length)
    } else if (event.key === 'Enter') {
      event.preventDefault()
      go(people[Math.min(active, people.length - 1)])
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="relative">
      <label htmlFor={id} className="sr-only">
        Find people
      </label>
      <input
        id={id}
        type="search"
        role="combobox"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={showList && people.length ? `${listId}-${active}` : undefined}
        autoComplete="off"
        spellCheck={false}
        autoFocus={autoFocus}
        placeholder="Find people by name or @username"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setActive(0)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={onKeyDown}
        className="h-11 w-full border-2 border-line-strong bg-surface px-3 text-ink placeholder:text-ink-3 focus:shadow-hard-sm focus:outline-none"
      />
      <ul
        id={listId}
        role="listbox"
        hidden={!showList}
        className="absolute inset-x-0 top-full z-20 mt-1 border-2 border-line-strong bg-surface shadow-hard"
      >
        {people.length === 0 ? (
          <li className="px-3 py-2 text-sm text-ink-3">No one matches “{q}”.</li>
        ) : (
          people.map((person, index) => (
            <li
              key={person.id}
              id={`${listId}-${index}`}
              role="option"
              aria-selected={index === active}
              onMouseDown={(e) => {
                e.preventDefault()
                go(person)
              }}
              onMouseEnter={() => setActive(index)}
              className={cn(
                'flex cursor-pointer items-center gap-3 px-3 py-2',
                index === active && 'bg-sunk',
              )}
            >
              <Avatar
                name={person.display_name}
                src={person.avatar_url}
                accent={person.accent_color as Accent}
                size="sm"
              />
              <span className="min-w-0 truncate">
                <span className="font-semibold">{person.display_name}</span>{' '}
                <span className="font-mono text-xs text-ink-3">@{person.username}</span>
              </span>
            </li>
          ))
        )}
      </ul>
    </div>
  )
}
