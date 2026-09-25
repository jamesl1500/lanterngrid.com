'use client'

import { Alert, Avatar, Button, cn, Select, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import { useRouter } from 'next/navigation'
import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'
import { flushSync } from 'react-dom'

import { browserApi } from '@/lib/api'
import { activeToken, insertAt, tagText } from '@/lib/composer'
import { attempt } from '@/lib/errors'
import { searchPeople } from '@/lib/people'
import { MAX_POST_LENGTH, type Visibility } from '@/lib/posts'
import { suggestTags } from '@/lib/tags'
import type { Me } from '@/lib/session'

import { MarkdownPreview } from './markdown-preview'

type Suggestion = { key: string; label: string; detail: string; insert: string }

type Props = {
  me: Pick<Me, 'display_name' | 'avatar_url' | 'accent_color'>
  /** Set to edit an existing post instead of writing a new one. */
  editing?: { id: string; body_md: string; visibility: Visibility }
}

async function suggestionsFor(trigger: '@' | '#', query: string): Promise<Suggestion[]> {
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

/** Write or edit a post: Markdown with a preview, and @/# autocomplete. */
export function Composer({ me, editing }: Props) {
  const router = useRouter()
  const id = useId()
  const textarea = useRef<HTMLTextAreaElement>(null)
  const [body, setBody] = useState(editing?.body_md ?? '')
  const [visibility, setVisibility] = useState<Visibility>(editing?.visibility ?? 'public')
  const [tab, setTab] = useState<'write' | 'preview'>('write')
  const [caret, setCaret] = useState(0)
  const [results, setResults] = useState<{ query: string; items: Suggestion[] } | null>(null)
  const [active, setActive] = useState(0)
  const [dismissed, setDismissed] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const token = activeToken(body, caret)
  const tokenKey = token && token.query ? `${token.trigger}${token.query}` : null
  const suggestions = tokenKey && results?.query === tokenKey ? results.items : []
  const showSuggestions = tab === 'write' && suggestions.length > 0 && dismissed !== tokenKey
  const remaining = MAX_POST_LENGTH - body.length
  const listId = `${id}-suggestions`

  useEffect(() => {
    if (!tokenKey) return
    let cancelled = false
    const timer = setTimeout(async () => {
      try {
        const items = await suggestionsFor(tokenKey[0] as '@' | '#', tokenKey.slice(1))
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
    const next = insertAt(body, token, suggestion.insert)
    // Commit the new text now so the caret lands before the next keystroke does.
    flushSync(() => {
      setBody(next.text)
      setCaret(next.caret)
      setActive(0)
    })
    textarea.current?.focus()
    textarea.current?.setSelectionRange(next.caret, next.caret)
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault()
      void submit()
      return
    }
    if (!showSuggestions) return
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

  async function submit() {
    if (!body.trim() || remaining < 0 || busy) return
    setBusy(true)
    setError(null)
    const result = await attempt(() =>
      editing
        ? browserApi.PATCH('/v1/posts/{post_id}', {
            params: { path: { post_id: editing.id } },
            body: { body_md: body, visibility },
          })
        : browserApi.POST('/v1/posts', { body: { body_md: body, visibility } }),
    )
    setBusy(false)
    if (!result.ok) {
      setError(Object.values(result.problem.fields)[0] ?? result.problem.message)
      return
    }
    if (editing) {
      router.push(`/p/${editing.id}` as Route)
    } else {
      setBody('')
      setTab('write')
    }
    router.refresh()
  }

  const tabClass = (t: typeof tab) =>
    cn(
      'border-b-4 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.08em]',
      tab === t ? 'border-cyan text-ink' : 'border-transparent text-ink-3 hover:text-ink',
    )

  return (
    <section
      aria-label={editing ? 'Edit post' : 'New post'}
      className="border-2 border-line-strong bg-surface shadow-hard"
    >
      <div className="flex items-center gap-3 border-b border-line px-4 pt-3">
        <Avatar
          name={me.display_name}
          src={me.avatar_url}
          accent={me.accent_color as Accent}
          size="sm"
        />
        <div role="tablist" aria-label="Composer" className="flex">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'write'}
            className={tabClass('write')}
            onClick={() => setTab('write')}
          >
            Write
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'preview'}
            className={tabClass('preview')}
            onClick={() => setTab('preview')}
          >
            Preview
          </button>
        </div>
      </div>

      <div className="relative">
        {tab === 'write' ? (
          <>
            <label htmlFor={id} className="sr-only">
              {editing ? 'Edit your post' : 'Write a post'}
            </label>
            <textarea
              id={id}
              ref={textarea}
              value={body}
              rows={editing ? 8 : 4}
              placeholder="What did you ship, break or learn? Markdown works, ```lang for code, #tags and @people too."
              role="combobox"
              aria-expanded={showSuggestions}
              aria-controls={listId}
              aria-autocomplete="list"
              aria-activedescendant={showSuggestions ? `${listId}-${active}` : undefined}
              onChange={(e) => {
                setBody(e.target.value)
                setCaret(e.target.selectionStart)
                setActive(0)
                setDismissed(null)
              }}
              onSelect={(e) => setCaret(e.currentTarget.selectionStart)}
              onKeyDown={onKeyDown}
              onBlur={() => setDismissed(tokenKey)}
              className="block min-h-28 w-full resize-y bg-transparent px-4 py-3 text-ink placeholder:text-ink-3 focus:outline-none"
            />
            <ul
              id={listId}
              role="listbox"
              hidden={!showSuggestions}
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
          </>
        ) : (
          <div className="min-h-28 px-4 py-3">
            {body.trim() ? (
              <MarkdownPreview source={body} />
            ) : (
              <p className="text-ink-3">Nothing to preview yet.</p>
            )}
          </div>
        )}
      </div>

      {error ? (
        <Alert tone="error" className="mx-4 mb-3">
          {error}
        </Alert>
      ) : null}

      <div className="flex flex-wrap items-center gap-3 border-t border-line px-4 py-2.5">
        <Select
          aria-label="Who can see this"
          value={visibility}
          onChange={(e) => setVisibility(e.target.value as Visibility)}
          className="w-40 [&_select]:h-8 [&_select]:text-sm"
        >
          <option value="public">Everyone</option>
          <option value="friends">Friends only</option>
        </Select>
        <span
          className={cn(
            'ml-auto font-mono text-xs',
            remaining < 0 ? 'text-coral' : remaining < 200 ? 'text-amber' : 'text-ink-3',
          )}
        >
          {remaining}
        </span>
        {editing ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/p/${editing.id}` as Route)}
          >
            Cancel
          </Button>
        ) : null}
        <Button
          type="button"
          size="sm"
          variant="accent"
          disabled={busy || !body.trim() || remaining < 0}
          onClick={() => void submit()}
        >
          {busy ? 'Posting…' : editing ? 'Save' : 'Post'}
        </Button>
      </div>
    </section>
  )
}
