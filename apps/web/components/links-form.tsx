'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import type { Schemas } from '@lanterngrid/api-client'
import { Alert, Button, Input, Select } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useFieldArray, useForm, useWatch } from 'react-hook-form'
import type { z } from 'zod'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { linkKinds, MAX_LINKS } from '@/lib/links'
import { linksSchema } from '@/lib/validation'

type Values = z.infer<typeof linksSchema>

export function LinksForm({ links }: { links: Schemas['ProfileLinkOut'][] }) {
  const router = useRouter()
  const [status, setStatus] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<Values>({ resolver: zodResolver(linksSchema), defaultValues: { links } })
  const { fields, append, remove, move } = useFieldArray({ control, name: 'links' })
  const kinds = useWatch({ control, name: 'links' })

  const onSubmit = handleSubmit(async (values) => {
    setStatus(null)
    const result = await attempt(() => browserApi.PUT('/v1/me/links', { body: values }))
    if (!result.ok) {
      setStatus({ tone: 'error', text: result.problem.message })
      return
    }
    reset({ links: result.data })
    setStatus({ tone: 'success', text: 'Links saved.' })
    router.refresh()
  })

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-4">
      {status ? <Alert tone={status.tone}>{status.text}</Alert> : null}
      {fields.length === 0 ? (
        <p className="text-sm text-ink-3">No links yet. Add your GitHub, blog or socials.</p>
      ) : (
        <ol className="grid gap-3">
          {fields.map((field, index) => {
            const error = errors.links?.[index]?.url?.message
            const kind = kinds[index]?.kind
            const placeholder = linkKinds.find((k) => k.value === kind)?.placeholder
            return (
              <li key={field.id} className="grid gap-1.5">
                <div className="grid grid-cols-[8.5rem_1fr] gap-2 sm:grid-cols-[9.5rem_1fr_auto]">
                  <Select
                    aria-label={`Link ${index + 1} type`}
                    {...register(`links.${index}.kind`)}
                  >
                    {linkKinds.map((k) => (
                      <option key={k.value} value={k.value}>
                        {k.label}
                      </option>
                    ))}
                  </Select>
                  <Input
                    type="url"
                    aria-label={`Link ${index + 1} address`}
                    placeholder={placeholder}
                    aria-invalid={error ? true : undefined}
                    aria-describedby={error ? `link-${index}-error` : undefined}
                    {...register(`links.${index}.url`)}
                  />
                  <div className="col-span-2 flex gap-1 sm:col-span-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-10"
                      aria-label={`Move link ${index + 1} up`}
                      disabled={index === 0}
                      onClick={() => move(index, index - 1)}
                    >
                      ↑
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-10"
                      aria-label={`Remove link ${index + 1}`}
                      onClick={() => remove(index)}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
                {error ? (
                  <p id={`link-${index}-error`} className="text-sm text-coral">
                    {error}
                  </p>
                ) : null}
              </li>
            )
          })}
        </ol>
      )}
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="secondary"
          disabled={fields.length >= MAX_LINKS}
          onClick={() => append({ kind: fields.length === 0 ? 'github' : 'website', url: '' })}
        >
          Add link
        </Button>
        <Button type="submit" disabled={isSubmitting || !isDirty}>
          {isSubmitting ? 'Saving…' : 'Save links'}
        </Button>
      </div>
    </form>
  )
}
