'use client'

import { Alert, Avatar, Button, cn, Select, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useRef, useState, type ChangeEvent } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import {
  achievementInfo,
  MAX_ACHIEVEMENT_TITLE,
  MAX_IMAGES,
  MAX_POST_LENGTH,
  type Achievement,
  type AchievementType,
  type PostImage,
  type Visibility,
} from '@/lib/posts'
import type { Me } from '@/lib/session'
import { imageProblem, imageTypes, uploadFile } from '@/lib/uploads'

import { AutocompleteTextarea } from './autocomplete-textarea'
import { MarkdownPreview } from './markdown-preview'

type Props = {
  me: Pick<Me, 'display_name' | 'avatar_url' | 'accent_color'>
  /** Set to edit an existing post instead of writing a new one. */
  editing?: {
    id: string
    body_md: string
    visibility: Visibility
    images: PostImage[]
    achievement: Achievement | null
  }
}

const achievementTypes = Object.entries(achievementInfo) as [
  AchievementType,
  (typeof achievementInfo)[AchievementType],
][]

/** An image in the post. `key` is null while it uploads; `preview` is a blob or public URL. */
type Attachment = { id: string; preview: string; key: string | null; alt: string }

/** Write or edit a post (or an achievement): Markdown with a preview, and @/# autocomplete. */
export function Composer({ me, editing }: Props) {
  const router = useRouter()
  const fileInput = useRef<HTMLInputElement>(null)
  const [body, setBody] = useState(editing?.body_md ?? '')
  const [visibility, setVisibility] = useState<Visibility>(editing?.visibility ?? 'public')
  const [images, setImages] = useState<Attachment[]>(
    () => editing?.images.map((i) => ({ id: i.key, preview: i.url, key: i.key, alt: i.alt })) ?? [],
  )
  // Null for a plain update; set while writing (or editing) an achievement.
  const [achievement, setAchievement] = useState<Achievement | null>(editing?.achievement ?? null)
  const [tab, setTab] = useState<'write' | 'preview'>('write')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  // Blob URLs for local previews, released when the composer goes away.
  const blobs = useRef(new Set<string>())

  const remaining = MAX_POST_LENGTH - body.length
  const uploading = images.some((i) => i.key === null)
  const empty = achievement ? !achievement.title.trim() : !body.trim() && images.length === 0

  useEffect(() => {
    const urls = blobs.current
    return () => urls.forEach((url) => URL.revokeObjectURL(url))
  }, [])

  function release(preview: string) {
    if (blobs.current.delete(preview)) URL.revokeObjectURL(preview)
  }

  function removeImage(id: string) {
    const image = images.find((i) => i.id === id)
    if (image) release(image.preview)
    setImages((all) => all.filter((i) => i.id !== id))
  }

  async function attach(file: File) {
    const id = crypto.randomUUID()
    const preview = URL.createObjectURL(file)
    blobs.current.add(preview)
    setImages((all) => [...all, { id, preview, key: null, alt: '' }])
    const result = await uploadFile('post', file)
    if (result.ok) {
      setImages((all) => all.map((i) => (i.id === id ? { ...i, key: result.key } : i)))
    } else {
      release(preview)
      setImages((all) => all.filter((i) => i.id !== id))
      setError(result.message)
    }
  }

  function onPick(event: ChangeEvent<HTMLInputElement>) {
    const files = [...(event.target.files ?? [])]
    event.target.value = '' // so picking the same file again still fires
    setError(null)
    const room = MAX_IMAGES - images.length
    if (files.length > room) setError(`A post can have up to ${MAX_IMAGES} images.`)
    for (const file of files.slice(0, Math.max(room, 0))) {
      const problem = imageProblem('post', file)
      if (problem) setError(problem)
      else void attach(file)
    }
  }

  async function submit() {
    if (empty || uploading || remaining < 0 || busy) return
    setBusy(true)
    setError(null)
    const fields = {
      body_md: body,
      visibility,
      images: images.flatMap((i) => (i.key ? [{ key: i.key, alt: i.alt }] : [])),
      achievement: achievement && { ...achievement, title: achievement.title.trim() },
    }
    const result = await attempt(() =>
      editing
        ? browserApi.PATCH('/v1/posts/{post_id}', {
            params: { path: { post_id: editing.id } },
            body: fields,
          })
        : browserApi.POST('/v1/posts', { body: fields }),
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
      setAchievement(null)
      images.forEach((i) => release(i.preview))
      setImages([])
      setTab('write')
    }
    router.refresh()
  }

  const tabClass = (t: typeof tab) =>
    cn(
      'border-b-4 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.08em]',
      tab === t ? 'border-cyan text-ink' : 'border-transparent text-ink-3 hover:text-ink',
    )

  const headerLink =
    'grid h-7 place-items-center border border-line px-2 font-mono text-xs text-ink-2 hover:border-line-strong hover:text-ink'

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
        {editing ? null : (
          <div className="ml-auto flex gap-1.5 pb-1.5">
            <button
              type="button"
              aria-pressed={achievement !== null}
              aria-label="Achievement"
              title="Celebrate something you did"
              onClick={() => setAchievement((a) => (a ? null : { type: 'shipped', title: '' }))}
              className={cn(
                headerLink,
                achievement && 'border-amber bg-amber-soft text-amber hover:border-amber',
              )}
            >
              <span aria-hidden>
                🏆<span className="hidden sm:inline"> achievement</span>
              </span>
            </button>
            <Link
              href="/snippets/new"
              aria-label="New snippet"
              title="Save a snippet of code"
              className={headerLink}
            >
              <span aria-hidden>
                {'{ }'}
                <span className="hidden sm:inline"> snippet</span>
              </span>
            </Link>
          </div>
        )}
      </div>

      {achievement ? (
        <div className="grid grid-cols-1 gap-2 border-b border-line bg-amber-soft px-4 py-3 sm:grid-cols-[12rem_1fr]">
          <Select
            aria-label="Kind of achievement"
            value={achievement.type}
            onChange={(e) =>
              setAchievement({ ...achievement, type: e.target.value as AchievementType })
            }
            className="[&_select]:h-9 [&_select]:text-sm"
          >
            {achievementTypes.map(([type, info]) => (
              <option key={type} value={type}>
                {info.emoji} {info.label}
              </option>
            ))}
          </Select>
          <input
            aria-label="What did you do?"
            placeholder="What did you do? e.g. Shipped dark mode"
            maxLength={MAX_ACHIEVEMENT_TITLE}
            value={achievement.title}
            onChange={(e) => setAchievement({ ...achievement, title: e.target.value })}
            className="h-9 w-full border-2 border-line-strong bg-surface px-3 text-sm placeholder:text-ink-3 focus:border-amber focus:outline-none"
          />
        </div>
      ) : null}

      <div className="relative">
        {tab === 'write' ? (
          <AutocompleteTextarea
            label={editing ? 'Edit your post' : 'Write a post'}
            value={body}
            onChange={setBody}
            onSubmit={() => void submit()}
            triggers={['@', '#']}
            rows={editing ? 8 : 4}
            placeholder={
              achievement
                ? 'Tell the story (optional). Markdown, #tags and @people work here too.'
                : 'What did you ship, break or learn? Markdown works, ```lang for code, #tags and @people too.'
            }
            className="min-h-28"
          />
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

      {images.length > 0 ? (
        <ul aria-label="Images" className="grid grid-cols-2 gap-3 px-4 pb-3 sm:grid-cols-4">
          {images.map((image, index) => (
            <li key={image.id} className="grid content-start gap-1.5">
              <div className="relative aspect-square border-2 border-line-strong bg-sunk">
                {/* eslint-disable-next-line @next/next/no-img-element -- local blob previews */}
                <img
                  src={image.preview}
                  alt=""
                  className={cn('size-full object-cover', image.key === null && 'opacity-50')}
                />
                {image.key === null ? (
                  <span className="absolute inset-x-0 bottom-0 bg-surface/90 px-2 py-1 font-mono text-xs text-ink-2">
                    uploading…
                  </span>
                ) : null}
                <button
                  type="button"
                  aria-label={`Remove image ${index + 1}`}
                  onClick={() => removeImage(image.id)}
                  className="absolute top-1 right-1 grid size-7 place-items-center border-2 border-line-strong bg-surface font-mono text-sm hover:bg-coral hover:text-ground"
                >
                  ×
                </button>
              </div>
              <input
                aria-label={`Describe image ${index + 1}`}
                placeholder="Describe it (alt text)"
                maxLength={300}
                value={image.alt}
                onChange={(e) =>
                  setImages((all) =>
                    all.map((i) => (i.id === image.id ? { ...i, alt: e.target.value } : i)),
                  )
                }
                className="w-full border border-line bg-sunk px-2 py-1 text-xs placeholder:text-ink-3 focus:border-line-strong focus:outline-none"
              />
            </li>
          ))}
        </ul>
      ) : null}

      {error ? (
        <Alert tone="error" className="mx-4 mb-3">
          {error}
        </Alert>
      ) : null}

      <div className="flex flex-wrap items-center gap-3 border-t border-line px-4 py-2.5">
        <input
          ref={fileInput}
          type="file"
          accept={imageTypes.join(',')}
          multiple
          hidden
          onChange={onPick}
        />
        <Button
          type="button"
          variant="secondary"
          size="sm"
          disabled={images.length >= MAX_IMAGES}
          onClick={() => fileInput.current?.click()}
          aria-label="Add image"
        >
          <span aria-hidden className="sm:hidden">
            Image
          </span>
          <span aria-hidden className="hidden sm:inline">
            Add image
          </span>
        </Button>
        <Select
          aria-label="Who can see this"
          value={visibility}
          onChange={(e) => setVisibility(e.target.value as Visibility)}
          className="w-36 sm:w-40 [&_select]:h-8 [&_select]:text-sm"
        >
          <option value="public">Everyone</option>
          <option value="friends">Friends only</option>
        </Select>
        {/* Only near the limit, so the toolbar fits on a phone. */}
        <span
          className={cn('ml-auto font-mono text-xs', remaining < 0 ? 'text-coral' : 'text-amber')}
        >
          {remaining < 200 ? remaining : null}
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
          disabled={busy || empty || uploading || remaining < 0}
          onClick={() => void submit()}
        >
          {busy ? 'Posting…' : editing ? 'Save' : 'Post'}
        </Button>
      </div>
    </section>
  )
}
