'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { Alert, Button, Field, TagInput, TextField } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import type { z } from 'zod'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { applyFieldErrors } from '@/lib/forms'
import { MAX_TAGS, suggestTags } from '@/lib/tags'
import { onboardingSchema, USERNAME_PATTERN } from '@/lib/validation'

type Values = z.infer<typeof onboardingSchema>
type Availability = 'checking' | 'available' | 'taken' | 'reserved' | null

const availabilityHint: Record<Exclude<Availability, null>, string> = {
  checking: 'Checking…',
  available: 'Available.',
  taken: 'Someone already has this one.',
  reserved: 'That name is reserved. Pick another.',
}

export function OnboardingForm({
  suggestedUsername,
  displayName,
}: {
  suggestedUsername?: string
  displayName: string
}) {
  const router = useRouter()
  const [problem, setProblem] = useState<string | null>(null)
  const [checked, setChecked] = useState<{ username: string; result: Availability } | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    control,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      username: suggestedUsername ?? '',
      display_name: displayName,
      headline: '',
      tags: [],
    },
  })

  const username = useWatch({ control, name: 'username' }).trim()
  const valid = USERNAME_PATTERN.test(username)
  const availability: Availability = !valid
    ? null
    : checked?.username === username
      ? checked.result
      : 'checking'

  useEffect(() => {
    if (!valid) return
    const timer = setTimeout(async () => {
      const result = await attempt(() =>
        browserApi.GET('/v1/usernames/{username}', { params: { path: { username } } }),
      )
      setChecked({
        username,
        result: !result.ok
          ? null
          : result.data.available
            ? 'available'
            : (result.data.problem as Availability),
      })
    }, 350)
    return () => clearTimeout(timer)
  }, [username, valid])

  const onSubmit = handleSubmit(async (values) => {
    setProblem(null)
    const result = await attempt(() =>
      browserApi.POST('/v1/me/onboarding', {
        body: { ...values, headline: values.headline || null },
      }),
    )
    if (!result.ok) {
      setProblem(result.problem.message)
      applyFieldErrors(setError, result.problem.fields)
      return
    }
    router.push(`/u/${result.data.username}`)
    router.refresh()
  })

  const usernameError =
    errors.username?.message ??
    (availability === 'taken' || availability === 'reserved'
      ? availabilityHint[availability]
      : undefined)

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-4">
      {problem ? <Alert tone="error">{problem}</Alert> : null}
      <TextField
        id="username"
        label="Username"
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        hint={
          availability === 'available' ? (
            <span className="text-lime">lanterngrid.com/u/{username} is yours to take.</span>
          ) : availability === 'checking' ? (
            availabilityHint.checking
          ) : (
            'Letters, numbers, dashes and underscores. This is your profile address.'
          )
        }
        error={usernameError}
        {...register('username')}
      />
      <TextField
        id="display_name"
        label="Name"
        autoComplete="name"
        error={errors.display_name?.message}
        {...register('display_name')}
      />
      <TextField
        id="headline"
        label="Headline"
        placeholder="Backend engineer, Rust and Postgres"
        hint="Optional. One line about what you build."
        error={errors.headline?.message}
        {...register('headline')}
      />
      <Field
        id="tags"
        label="Your stack"
        hint="Optional. Languages, tools and topics you work with. Press Enter to add."
        error={errors.tags?.message}
      >
        <Controller
          control={control}
          name="tags"
          render={({ field }) => (
            <TagInput
              id="tags"
              value={field.value}
              onChange={field.onChange}
              suggest={suggestTags}
              max={MAX_TAGS}
              accent="violet"
              placeholder="TypeScript, Postgres, distributed systems…"
              aria-describedby={errors.tags ? 'tags-error' : 'tags-hint'}
            />
          )}
        />
      </Field>
      <Button type="submit" size="lg" variant="accent" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : 'Create my profile'}
      </Button>
    </form>
  )
}
