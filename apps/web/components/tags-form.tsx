'use client'

import type { Schemas } from '@lanterngrid/api-client'
import { Alert, Button, Field, TagInput, type Accent } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { MAX_TAGS, suggestTags } from '@/lib/tags'

export function TagsForm({ tags, accent }: { tags: Schemas['TagOut'][]; accent: Accent }) {
  const router = useRouter()
  const [saved, setSaved] = useState(() => tags.map((t) => t.name))
  const [value, setValue] = useState(saved)
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const dirty = value.join('\n') !== saved.join('\n')

  async function save() {
    setSaving(true)
    setStatus(null)
    const result = await attempt(() => browserApi.PUT('/v1/me/tags', { body: { tags: value } }))
    setSaving(false)
    if (!result.ok) {
      setStatus({
        tone: 'error',
        text: Object.values(result.problem.fields)[0] ?? result.problem.message,
      })
      return
    }
    const names = result.data.map((t) => t.name)
    setSaved(names)
    setValue(names)
    setStatus({ tone: 'success', text: 'Stack saved.' })
    router.refresh()
  }

  return (
    <div className="grid gap-4">
      {status ? <Alert tone={status.tone}>{status.text}</Alert> : null}
      <Field
        id="stack"
        label="Your stack"
        hint={`Languages, tools and topics you work with. Up to ${MAX_TAGS}; press Enter to add.`}
      >
        <TagInput
          id="stack"
          value={value}
          onChange={setValue}
          suggest={suggestTags}
          max={MAX_TAGS}
          accent={accent}
          placeholder="TypeScript, Postgres, distributed systems…"
          aria-describedby="stack-hint"
        />
      </Field>
      <Button
        type="button"
        className="justify-self-start"
        disabled={saving || !dirty}
        onClick={() => void save()}
      >
        {saving ? 'Saving…' : 'Save stack'}
      </Button>
    </div>
  )
}
