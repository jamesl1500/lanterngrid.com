'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import type { Schemas } from '@lanterngrid/api-client'
import { AccentPicker, Alert, Button, TextAreaField, TextField } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import type { z } from 'zod'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { applyFieldErrors } from '@/lib/forms'
import { profileSchema } from '@/lib/validation'

type Values = z.infer<typeof profileSchema>

export function ProfileForm({ profile }: { profile: Schemas['ProfileSettings'] }) {
  const router = useRouter()
  const [status, setStatus] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const {
    register,
    control,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<Values>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      display_name: profile.display_name,
      headline: profile.headline ?? '',
      bio: profile.bio ?? '',
      location: profile.location ?? '',
      website: profile.website ?? '',
      accent_color: profile.accent_color,
    },
  })

  const onSubmit = handleSubmit(async (values) => {
    setStatus(null)
    const result = await attempt(() => browserApi.PATCH('/v1/me/profile', { body: values }))
    if (!result.ok) {
      setStatus({ tone: 'error', text: result.problem.message })
      applyFieldErrors(setError, result.problem.fields)
      return
    }
    reset(values)
    setStatus({ tone: 'success', text: 'Profile saved.' })
    router.refresh()
  })

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-5">
      {status ? <Alert tone={status.tone}>{status.text}</Alert> : null}
      <TextField
        id="display_name"
        label="Name"
        error={errors.display_name?.message}
        {...register('display_name')}
      />
      <TextField
        id="headline"
        label="Headline"
        placeholder="Backend engineer, Rust and Postgres"
        error={errors.headline?.message}
        {...register('headline')}
      />
      <TextAreaField
        id="bio"
        label="Bio"
        rows={5}
        hint="What you work on, what you're learning, what you'd like to talk about."
        error={errors.bio?.message}
        {...register('bio')}
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="location"
          label="Location"
          error={errors.location?.message}
          {...register('location')}
        />
        <TextField
          id="website"
          label="Website"
          type="url"
          placeholder="https://you.dev"
          error={errors.website?.message}
          {...register('website')}
        />
      </div>
      <Controller
        control={control}
        name="accent_color"
        render={({ field }) => (
          <AccentPicker
            name={field.name}
            value={field.value}
            onChange={field.onChange}
            label="Profile accent"
          />
        )}
      />
      <Button type="submit" className="justify-self-start" disabled={isSubmitting || !isDirty}>
        {isSubmitting ? 'Saving…' : 'Save profile'}
      </Button>
    </form>
  )
}
