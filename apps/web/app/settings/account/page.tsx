import { Alert, Button, Card } from '@lanterngrid/ui'
import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import {
  ResendVerificationButton,
  SendPasswordResetButton,
  SignOutEverywhereButton,
} from '@/components/account-actions'
import { GitHubMark } from '@/components/auth/github-button'
import { githubStartUrl } from '@/lib/routes'
import { getProviders, requireMe } from '@/lib/session'

export const metadata: Metadata = { title: 'Account settings' }

const errorMessages: Record<string, string> = {
  github_other_account:
    'That GitHub account is already connected to a different Lantern Grid account.',
  github_state: 'Connecting GitHub was interrupted. Try again.',
  github_failed: "GitHub didn't let us read your profile. Try again.",
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="grid gap-3 border-t border-line pt-5 first:border-t-0 first:pt-0">
      <h3 className="text-lg font-semibold">{title}</h3>
      {children}
    </section>
  )
}

export default async function AccountSettingsPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>
}) {
  const me = await requireMe('/settings/account')
  const { github } = await getProviders()
  const { error } = await searchParams

  return (
    <Card className="grid gap-6 p-6">
      <header className="grid gap-1">
        <h2 className="text-xl font-bold">Account</h2>
        <p className="text-sm text-ink-2">Only you can see this page.</p>
      </header>
      {error && errorMessages[error] ? <Alert tone="error">{errorMessages[error]}</Alert> : null}

      <Section title="Email">
        <p className="font-mono text-sm">
          {me.email}{' '}
          <span className={me.email_verified ? 'text-lime' : 'text-amber'}>
            {me.email_verified ? '· verified' : '· not verified yet'}
          </span>
        </p>
        {me.email_verified ? null : <ResendVerificationButton />}
      </Section>

      <Section title="GitHub">
        {me.github_login ? (
          <p className="flex items-center gap-2 text-sm">
            <GitHubMark className="size-4" /> Connected as{' '}
            <a
              href={`https://github.com/${me.github_login}`}
              className="font-mono text-cyan underline-offset-2 hover:underline"
              target="_blank"
              rel="noopener"
            >
              @{me.github_login}
            </a>
          </p>
        ) : github ? (
          <>
            <p className="text-sm text-ink-2">
              Connect GitHub to sign in with it. Later you&apos;ll be able to share your repos.
            </p>
            <Button asChild variant="secondary" size="sm" className="justify-self-start">
              <a href={githubStartUrl('/settings/account')}>
                <GitHubMark className="size-4" /> Connect GitHub
              </a>
            </Button>
          </>
        ) : (
          <p className="text-sm text-ink-3">GitHub sign-in isn&apos;t switched on here yet.</p>
        )}
      </Section>

      <Section title="Password">
        <p className="text-sm text-ink-2">
          {me.has_password
            ? "To change your password, we'll email you a link."
            : "You sign in with GitHub. Set a password too if you'd like another way in."}
        </p>
        <SendPasswordResetButton email={me.email} />
      </Section>

      <Section title="Sessions">
        <p className="text-sm text-ink-2">
          Signed in somewhere you shouldn&apos;t be? This signs you out on every browser, including
          this one.
        </p>
        <SignOutEverywhereButton />
      </Section>
    </Card>
  )
}
