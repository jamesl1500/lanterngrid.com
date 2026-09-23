'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { Alert, Button, TextField } from '@lanterngrid/ui'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { z } from 'zod'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { forgotPasswordSchema } from '@/lib/validation'

type Values = z.infer<typeof forgotPasswordSchema>

export function ForgotPasswordForm() {
  const [sentTo, setSentTo] = useState<string | null>(null)
  const [problem, setProblem] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(forgotPasswordSchema), defaultValues: { email: '' } })

  const onSubmit = handleSubmit(async (values) => {
    setProblem(null)
    const result = await attempt(() => browserApi.POST('/v1/auth/password-reset', { body: values }))
    if (!result.ok) return setProblem(result.problem.message)
    setSentTo(values.email)
  })

  if (sentTo) {
    return (
      <Alert tone="success">
        If <strong>{sentTo}</strong> has an account, a reset link is on its way. It works for one
        hour.
      </Alert>
    )
  }

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-4">
      {problem ? <Alert tone="error">{problem}</Alert> : null}
      <TextField
        id="email"
        label="Email"
        type="email"
        autoComplete="email"
        error={errors.email?.message}
        {...register('email')}
      />
      <Button type="submit" size="lg" disabled={isSubmitting}>
        {isSubmitting ? 'Sending…' : 'Email me a reset link'}
      </Button>
    </form>
  )
}
