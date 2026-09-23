import { Alert, Button } from '@lanterngrid/ui'
import type { Metadata } from 'next'
import Link from 'next/link'

import { AuthCard } from '@/components/auth/auth-card'
import { ResetPasswordForm } from '@/components/auth/reset-password-form'

export const metadata: Metadata = { title: 'Choose a new password' }

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>
}) {
  const { token } = await searchParams
  return (
    <AuthCard eyebrow="account recovery" title="Choose a new password">
      {token ? (
        <ResetPasswordForm token={token} />
      ) : (
        <div className="grid gap-4">
          <Alert tone="error">
            This link is missing its code. Open the link from the email again.
          </Alert>
          <Button asChild variant="secondary">
            <Link href="/forgot-password">Send a new link</Link>
          </Button>
        </div>
      )}
    </AuthCard>
  )
}
