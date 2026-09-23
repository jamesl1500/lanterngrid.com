'use client'

import { useEffect, useId, useState, type KeyboardEvent } from 'react'

import { cn } from '../lib/cn'
import { accentClasses, type Accent } from '../lib/kinds'

export type TagSuggestion = { slug: string; name: string }

export type TagInputProps = {
  id?: string
  /** Tag names in order. */
  value: string[]
  onChange: (tags: string[]) => void
  /** Called as the person types (debounced). Return matches to offer. */
  suggest?: (query: string) => Promise<TagSuggestion[]>
  max?: number
  accent?: Accent
  placeholder?: string
  invalid?: boolean
  'aria-describedby'?: string
}

const sameTag = (a: string, b: string) => a.trim().toLowerCase() === b.trim().toLowerCase()

/**
 * Type a tag and press Enter or comma to add it. Backspace in the empty box removes the last
 * one. Arrow keys move through suggestions.
 */
export function TagInput({
  id: idProp,
  value,
  onChange,
  suggest,
  max = 12,
  accent = 'cyan',
  placeholder = 'Add a tag',
  invalid,
  'aria-describedby': describedBy,
}: TagInputProps) {
  const autoId = useId()
  const id = idProp ?? autoId
  const listId = `${id}-suggestions`
  const [draft, setDraft] = useState('')
  const [results, setResults] = useState<{ query: string; tags: TagSuggestion[] } | null>(null)
  const [active, setActive] = useState(0)
  const [open, setOpen] = useState(false)
  const c = accentClasses[accent]
  const full = value.length >= max
  const query = draft.trim()

  // Only show results for what's typed now, minus tags already picked.
  const options =
    results && results.query === query
      ? results.tags.filter((t) => !value.some((v) => sameTag(v, t.name))).slice(0, 8)
      : []
  const showList = open && !full && options.length > 0

  useEffect(() => {
    if (!suggest || full) return
    let cancelled = false
    const timer = setTimeout(async () => {
      try {
        const tags = await suggest(query)
        if (!cancelled) setResults({ query, tags })
      } catch {
        // Suggestions are a nicety; typing still works without them.
      }
    }, 200)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [query, suggest, full])

  function add(name: string) {
    const clean = name.trim().replace(/\s+/g, ' ')
    if (!clean || full || value.some((v) => sameTag(v, clean))) {
      setDraft('')
      return
    }
    onChange([...value, clean])
    setDraft('')
    setActive(0)
  }

  function remove(index: number) {
    onChange(value.filter((_, i) => i !== index))
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault()
      const picked = showList ? options[Math.min(active, options.length - 1)] : undefined
      add(picked?.name ?? draft)
    } else if (event.key === 'Backspace' && draft === '' && value.length > 0) {
      remove(value.length - 1)
    } else if (event.key === 'ArrowDown' && options.length > 0) {
      event.preventDefault()
      setOpen(true)
      setActive((i) => (i + 1) % options.length)
    } else if (event.key === 'ArrowUp' && options.length > 0) {
      event.preventDefault()
      setActive((i) => (i - 1 + options.length) % options.length)
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="relative">
      <div
        className={cn(
          'flex min-h-10 flex-wrap items-center gap-1.5 border-2 border-line-strong bg-surface px-2 py-1.5',
          'focus-within:shadow-hard-sm',
          invalid && 'border-coral',
        )}
      >
        {value.map((tag, index) => (
          <span
            key={tag}
            className={cn(
              'inline-flex items-center gap-1 border pl-1.5 font-mono text-xs',
              c.soft,
              c.text,
              c.border,
            )}
          >
            {tag}
            <button
              type="button"
              onClick={() => remove(index)}
              aria-label={`Remove ${tag}`}
              className="px-1 hover:bg-ink hover:text-ground"
            >
              ×
            </button>
          </span>
        ))}
        <input
          id={id}
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={showList ? `${listId}-${active}` : undefined}
          aria-invalid={invalid ? true : undefined}
          aria-describedby={describedBy}
          value={draft}
          disabled={full}
          placeholder={full ? `${max} tags max` : value.length ? '' : placeholder}
          onChange={(e) => {
            setDraft(e.target.value)
            setActive(0)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
          className="h-7 min-w-24 flex-1 bg-transparent text-ink placeholder:text-ink-3 focus:outline-none disabled:cursor-not-allowed"
        />
      </div>
      <ul
        id={listId}
        role="listbox"
        hidden={!showList}
        className="absolute inset-x-0 top-full z-20 mt-1 border-2 border-line-strong bg-surface shadow-hard"
      >
        {options.map((option, index) => (
          <li
            key={option.slug}
            id={`${listId}-${index}`}
            role="option"
            aria-selected={index === active}
            // mousedown, not click, so the input doesn't blur and close the list first.
            onMouseDown={(e) => {
              e.preventDefault()
              add(option.name)
            }}
            onMouseEnter={() => setActive(index)}
            className={cn(
              'cursor-pointer px-3 py-1.5 font-mono text-sm',
              index === active ? `${c.soft} ${c.text}` : 'text-ink-2',
            )}
          >
            {option.name}
          </li>
        ))}
      </ul>
    </div>
  )
}
