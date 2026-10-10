import type { Schemas } from '@lanterngrid/api-client'

export type ModerationCase = Schemas['CaseOut']
export type SubjectKind = ModerationCase['subject_kind']
export type ReportReason = Schemas['ReportOut']['reason']
export type CaseStatus = ModerationCase['status']

/** Matches `Details` in moderation/schemas.py. */
export const MAX_REPORT_DETAILS = 1000
export const MAX_CASE_NOTE = 500

export const reasons: { value: ReportReason; label: string; hint: string }[] = [
  { value: 'spam', label: 'Spam', hint: 'Ads, scams or the same thing over and over.' },
  { value: 'harassment', label: 'Harassment', hint: 'Bullying, threats or piling on someone.' },
  { value: 'hate', label: 'Hate', hint: 'Attacking people for who they are.' },
  { value: 'explicit', label: 'Explicit', hint: 'Sexual or graphic material.' },
  { value: 'impersonation', label: 'Impersonation', hint: 'Pretending to be someone else.' },
  { value: 'other', label: 'Something else', hint: 'Say what it is below.' },
]

export const reasonLabel = Object.fromEntries(reasons.map((r) => [r.value, r.label])) as Record<
  ReportReason,
  string
>

/** "this post", "this message", "@ada". */
export function subjectName(kind: SubjectKind, username?: string) {
  if (kind === 'user') return username ? `@${username}` : 'this person'
  return `this ${kind}`
}

export const statusLabel: Record<CaseStatus, string> = {
  open: 'open',
  dismissed: 'dismissed',
  removed: 'removed',
  suspended: 'author suspended',
}

/** Where a moderator can see the reported thing in place. Messages are private: none. */
export function subjectHref(c: ModerationCase): string | null {
  switch (c.subject_kind) {
    case 'post':
      return `/p/${c.subject_id}`
    case 'comment':
      return c.post_id ? `/p/${c.post_id}#comment-${c.subject_id}` : null
    case 'snippet':
      return `/snippets/${c.subject_id}`
    case 'user':
      return c.subject_author ? `/u/${c.subject_author.username}` : null
    case 'message':
      return null
  }
}

/** Tally of reasons across a case's reports, most common first: "spam ×3, hate". */
export function reasonSummary(reports: { reason: ReportReason }[]) {
  const counts = new Map<ReportReason, number>()
  for (const r of reports) counts.set(r.reason, (counts.get(r.reason) ?? 0) + 1)
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([reason, n]) => (n > 1 ? `${reasonLabel[reason]} ×${n}` : reasonLabel[reason]))
    .join(', ')
}
