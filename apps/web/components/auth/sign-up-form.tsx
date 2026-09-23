'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { Alert, Button, TextField } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { z } from 'zod'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { applyFieldErrors } from '@/lib/forms'
import { signUpSchema } from '@/lib/validation'

type Values = z.infer<typeof signUpSchema>

export function SignUpForm() {
  const router = useRouter()
  const [problem, setProblem] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(signUpSchema),
    defaultValues: { display_name: '', email: '', password: '' },
  })

  const onSubmit = handleSubmit(async (values) => {
    setProblem(null)
    const result = await attempt(() => browserApi.POST('/v1/auth/signup', { body: values }))
    if (!result.ok) {
      setProblem(result.problem.message)
      applyFieldErrors(setError, result.problem.fields)
      return
    }
    router.push('/onboarding')
    router.refresh()
  })

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-4">
      {problem ? <Alert tone="error">{problem}</Alert> : null}
      <TextField
        id="display_name"
        label="Name"
        autoComplete="name"
        error={errors.display_name?.message}
        {...register('display_name')}
      />
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
        autoComplete="new-password"
        hint="At least 10 characters. A short phrase works well."
        error={errors.password?.message}
        {...register('password')}
      />
      <Button type="submit" size="lg" variant="accent" disabled={isSubmitting}>
        {isSubmitting ? 'Creating your account…' : 'Create account'}
      </Button>
    </form>
  )
}
