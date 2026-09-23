'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { Alert, Button, TextField } from '@lanterngrid/ui'
import Link from 'next/link'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { z } from 'zod'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { applyFieldErrors } from '@/lib/forms'
import { resetPasswordSchema } from '@/lib/validation'

type Values = z.infer<typeof resetPasswordSchema>

export function ResetPasswordForm({ token }: { token: string }) {
  const [done, setDone] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: '' },
  })

  const onSubmit = handleSubmit(async ({ password }) => {
    setProblem(null)
    const result = await attempt(() =>
      browserApi.POST('/v1/auth/password-reset/confirm', { body: { token, password } }),
    )
    if (!result.ok) {
      setProblem(result.problem.message)
      applyFieldErrors(setError, result.problem.fields)
      return
    }
    setDone(true)
  })

  if (done) {
    return (
      <div className="grid gap-4">
        <Alert tone="success">
          Your password is changed and you&apos;re signed out on every device.
        </Alert>
        <Button asChild size="lg">
          <Link href="/signin">Sign in</Link>
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-4">
      {problem ? <Alert tone="error">{problem}</Alert> : null}
      <TextField
        id="password"
        label="New password"
        type="password"
        autoComplete="new-password"
        hint="At least 10 characters."
        error={errors.password?.message}
        {...register('password')}
      />
      <Button type="submit" size="lg" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : 'Set new password'}
      </Button>
    </form>
  )
}
