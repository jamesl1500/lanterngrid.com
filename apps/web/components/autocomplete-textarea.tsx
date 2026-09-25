'use client'

import { cn } from '@lanterngrid/ui'
import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'
import { flushSync } from 'react-dom'

import { activeToken, insertAt, tagText } from '@/lib/composer'
import { searchPeople } from '@/lib/people'
import { suggestTags } from '@/lib/tags'

type Trigger = '@' | '#'
type Suggestion = { key: string; label: string; detail: string; insert: string }

async function suggestionsFor(trigger: Trigger, query: string): Promise<Suggestion[]> {
  if (trigger === '@') {
    const people = await searchPeople(query)
    return people.map((p) => ({
      key: p.id,
      label: `@${p.username}`,
      detail: p.display_name,
      insert: `@${p.username}`,
    }))
  }
  const tags = await suggestTags(query)
  return tags.map((t) => ({ key: t.slug, label: `#${t.name}`, detail: t.kind, insert: tagText(t) }))
}

type Props = {
  label: string
  value: string
  onChange: (value: string) => void
  /** Called on Ctrl/Cmd+Enter. */
  onSubmit: () => void
  /** Which of @people and #tags to suggest. */
  triggers: Trigger[]
  rows?: number
  placeholder?: string
  className?: string
}

/** A textarea that suggests @people and #tags as you type them. */
export function AutocompleteTextarea({
  label,
  value,
  onChange,
  onSubmit,
  triggers,
  rows,
  placeholder,
  className,
}: Props) {
  const id = useId()
  const textarea = useRef<HTMLTextAreaElement>(null)
  const [caret, setCaret] = useState(0)
  const [results, setResults] = useState<{ query: string; items: Suggestion[] } | null>(null)
  const [active, setActive] = useState(0)
  const [dismissed, setDismissed] = useState<string | null>(null)

  const found = activeToken(value, caret)
  const token = found && triggers.includes(found.trigger) ? found : null
  const tokenKey = token && token.query ? `${token.trigger}${token.query}` : null
  const suggestions = tokenKey && results?.query === tokenKey ? results.items : []
  const open = suggestions.length > 0 && dismissed !== tokenKey
  const listId = `${id}-suggestions`

  useEffect(() => {
    if (!tokenKey) return
    let cancelled = false
    const timer = setTimeout(async () => {
      try {
        const items = await suggestionsFor(tokenKey[0] as Trigger, tokenKey.slice(1))
        if (!cancelled) setResults({ query: tokenKey, items: items.slice(0, 6) })
      } catch {
        // Autocomplete is a nicety; typing still works.
      }
    }, 150)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [tokenKey])

  function pick(suggestion: Suggestion | undefined) {
    if (!suggestion || !token) return
    const next = insertAt(value, token, suggestion.insert)
    // Commit the new text now so the caret lands before the next keystroke does.
    flushSync(() => {
      onChange(next.text)
      setCaret(next.caret)
      setActive(0)
    })
    textarea.current?.focus()
    textarea.current?.setSelectionRange(next.caret, next.caret)
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault()
      onSubmit()
      return
    }
    if (!open) return
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      const step = event.key === 'ArrowDown' ? 1 : -1
      setActive((i) => (i + step + suggestions.length) % suggestions.length)
    } else if (event.key === 'Enter' || event.key === 'Tab') {
      event.preventDefault()
      pick(suggestions[Math.min(active, suggestions.length - 1)])
    } else if (event.key === 'Escape') {
      setDismissed(tokenKey)
    }
  }

  return (
    <div className="relative">
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <textarea
        id={id}
        ref={textarea}
        value={value}
        rows={rows}
        placeholder={placeholder}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={open ? `${listId}-${active}` : undefined}
        onChange={(e) => {
          onChange(e.target.value)
          setCaret(e.target.selectionStart)
          setActive(0)
          setDismissed(null)
        }}
        onSelect={(e) => setCaret(e.currentTarget.selectionStart)}
        onKeyDown={onKeyDown}
        onBlur={() => setDismissed(tokenKey)}
        className={cn(
          'block w-full resize-y bg-transparent px-4 py-3 text-ink placeholder:text-ink-3 focus:outline-none',
          className,
        )}
      />
      <ul
        id={listId}
        role="listbox"
        hidden={!open}
        className="absolute inset-x-4 top-full z-20 -mt-2 border-2 border-line-strong bg-surface shadow-hard"
      >
        {suggestions.map((s, index) => (
          <li
            key={s.key}
            id={`${listId}-${index}`}
            role="option"
            aria-selected={index === active}
            onMouseDown={(e) => {
              e.preventDefault()
              pick(s)
            }}
            onMouseEnter={() => setActive(index)}
            className={cn(
              'flex cursor-pointer justify-between gap-3 px-3 py-1.5 font-mono text-sm',
              index === active ? 'bg-cyan-soft text-cyan' : 'text-ink-2',
            )}
          >
            <span>{s.label}</span>
            <span className="truncate text-xs text-ink-3">{s.detail}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
