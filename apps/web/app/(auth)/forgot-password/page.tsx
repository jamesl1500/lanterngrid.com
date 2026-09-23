import type { Metadata } from 'next'
import Link from 'next/link'

import { AuthCard } from '@/components/auth/auth-card'
import { ForgotPasswordForm } from '@/components/auth/forgot-password-form'

export const metadata: Metadata = { title: 'Reset your password' }

export default function ForgotPasswordPage() {
  return (
    <AuthCard
      eyebrow="account recovery"
      title="Reset your password"
      footer={
        <Link href="/signin" className="text-cyan underline-offset-2 hover:underline">
          Back to sign in
        </Link>
      }
    >
      <p className="text-ink-2">
        Enter the email you signed up with and we&apos;ll send you a link to choose a new password.
      </p>
      <ForgotPasswordForm />
    </AuthCard>
  )
}
