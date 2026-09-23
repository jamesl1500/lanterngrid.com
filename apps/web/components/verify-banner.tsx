import { getMe } from '@/lib/session'

import { ResendVerificationButton } from './account-actions'

/** Nudge for anyone who hasn't confirmed their email yet. */
export async function VerifyBanner() {
  const me = await getMe()
  if (!me || me.email_verified) return null
  return (
    <div className="border-b border-amber bg-amber-soft">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 text-sm">
        <span>
          Confirm <strong>{me.email}</strong> with the link we emailed you.
        </span>
        <ResendVerificationButton compact />
      </div>
    </div>
  )
}
