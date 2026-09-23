'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { Alert, Button, TextField } from '@lanterngrid/ui'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { z } from 'zod'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { applyFieldErrors } from '@/lib/forms'
import { homeFor } from '@/lib/routes'
import { signInSchema } from '@/lib/validation'

type Values = z.infer<typeof signInSchema>

export function SignInForm({ next }: { next?: string | null }) {
  const router = useRouter()
  const [problem, setProblem] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = handleSubmit(async (values) => {
    setProblem(null)
    const result = await attempt(() => browserApi.POST('/v1/auth/signin', { body: values }))
    if (!result.ok) {
      setProblem(result.problem.message)
      applyFieldErrors(setError, result.problem.fields)
      return
    }
    router.push(homeFor(result.data, next))
    router.refresh()
  })

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
      <TextField
        id="password"
        label="Password"
        type="password"
        autoComplete="current-password"
        error={errors.password?.message}
        hint={
          <Link href="/forgot-password" className="text-cyan underline-offset-2 hover:underline">
            Forgot your password?
          </Link>
        }
        {...register('password')}
      />
      <Button type="submit" size="lg" disabled={isSubmitting}>
        {isSubmitting ? 'Signing in…' : 'Sign in'}
      </Button>
    </form>
  )
}
