'use client'

import { Alert, Button, SelectField, TextAreaField, TextField } from '@lanterngrid/ui'
import type { Route } from 'next'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import type { Visibility } from '@/lib/posts'
import {
  languageFromFilename,
  languageLabels,
  languageOptions,
  MAX_SNIPPET_LENGTH,
  type Language,
  type Snippet,
} from '@/lib/snippets'

import { CodeEditor } from './code-editor'

type Props = { editing?: Snippet }

/** Write a new snippet or edit one of yours. */
export function SnippetForm({ editing }: Props) {
  const router = useRouter()
  const [title, setTitle] = useState(editing?.title ?? '')
  const [filename, setFilename] = useState(editing?.filename ?? '')
  const [language, setLanguage] = useState<Language>(editing?.language ?? 'text')
  // Until someone picks a language, the filename's extension decides it.
  const [pickedLanguage, setPickedLanguage] = useState(Boolean(editing))
  const [description, setDescription] = useState(editing?.description ?? '')
  const [visibility, setVisibility] = useState<Visibility>(editing?.visibility ?? 'public')
  const [content, setContent] = useState(editing?.content ?? '')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const tooLong = content.length > MAX_SNIPPET_LENGTH

  function onFilename(value: string) {
    setFilename(value)
    const guess = languageFromFilename(value)
    if (guess && !pickedLanguage) setLanguage(guess)
  }

  async function save() {
    if (busy) return
    if (!title.trim() || !content.trim()) {
      setErrors({
        ...(title.trim() ? {} : { title: 'Give it a title.' }),
        ...(content.trim() ? {} : { content: 'Add some code.' }),
      })
      return
    }
    setBusy(true)
    setError(null)
    setErrors({})
    const body = {
      title,
      filename: filename.trim() || null,
      language,
      content,
      description,
      visibility,
    }
    const result = await attempt(() =>
      editing
        ? browserApi.PATCH('/v1/snippets/{snippet_id}', {
            params: { path: { snippet_id: editing.id } },
            body,
          })
        : browserApi.POST('/v1/snippets', { body }),
    )
    setBusy(false)
    if (!result.ok) {
      setErrors(result.problem.fields)
      setError(result.problem.message)
      return
    }
    router.push(`/snippets/${result.data.id}` as Route)
    router.refresh()
  }

  return (
    <form
      className="grid gap-5"
      onSubmit={(e) => {
        e.preventDefault()
        void save()
      }}
    >
      <div className="grid gap-4 sm:grid-cols-[2fr_1fr]">
        <TextField
          id="snippet-title"
          label="Title"
          value={title}
          maxLength={100}
          onChange={(e) => setTitle(e.target.value)}
          error={errors.title}
          placeholder="Keyset pagination in one query"
        />
        <TextField
          id="snippet-filename"
          label="Filename (optional)"
          value={filename}
          maxLength={100}
          onChange={(e) => onFilename(e.target.value)}
          error={errors.filename}
          placeholder="feed.sql"
          className="font-mono"
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField
          id="snippet-language"
          label="Language"
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value as Language)
            setPickedLanguage(true)
          }}
        >
          {languageOptions.map((l) => (
            <option key={l} value={l}>
              {languageLabels[l]}
            </option>
          ))}
        </SelectField>
        <SelectField
          id="snippet-visibility"
          label="Who can see it"
          value={visibility}
          onChange={(e) => setVisibility(e.target.value as Visibility)}
        >
          <option value="public">Everyone</option>
          <option value="friends">Friends only</option>
        </SelectField>
      </div>
      <div className="grid gap-1.5">
        <span
          id="snippet-code-label"
          className="font-mono text-xs tracking-[0.08em] text-ink-2 uppercase"
        >
          Code
        </span>
        <CodeEditor
          initialValue={content}
          onChange={setContent}
          language={language}
          labelledBy="snippet-code-label"
          onSubmit={() => void save()}
        />
        {errors.content || tooLong ? (
          <p className="text-sm text-coral">
            {errors.content ?? `Snippets can be up to ${MAX_SNIPPET_LENGTH} characters.`}
          </p>
        ) : null}
      </div>
      <TextAreaField
        id="snippet-description"
        label="Description (optional)"
        rows={2}
        maxLength={500}
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        error={errors.description}
        placeholder="What it does, and anything worth knowing before you use it."
      />
      {error && Object.keys(errors).length === 0 ? <Alert tone="error">{error}</Alert> : null}
      <div className="flex gap-3">
        <Button type="submit" variant="accent" disabled={busy || tooLong}>
          {busy ? 'Saving…' : editing ? 'Save snippet' : 'Create snippet'}
        </Button>
        <Button
          type="button"
          variant="ghost"
          onClick={() => router.push((editing ? `/snippets/${editing.id}` : '/') as Route)}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}
