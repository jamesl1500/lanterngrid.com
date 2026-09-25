import type { Schemas } from '@lanterngrid/api-client'

export type LinkKind = Schemas['ProfileLinkIn']['kind']

export const MAX_LINKS = 8

export const LINK_KINDS = [
  'github',
  'gitlab',
  'linkedin',
  'x',
  'mastodon',
  'bluesky',
  'website',
  'blog',
  'youtube',
  'other',
] as const satisfies readonly LinkKind[]

export const linkKinds: { value: LinkKind; label: string; placeholder: string }[] = [
  { value: 'github', label: 'GitHub', placeholder: 'https://github.com/you' },
  { value: 'gitlab', label: 'GitLab', placeholder: 'https://gitlab.com/you' },
  { value: 'linkedin', label: 'LinkedIn', placeholder: 'https://linkedin.com/in/you' },
  { value: 'x', label: 'X', placeholder: 'https://x.com/you' },
  { value: 'mastodon', label: 'Mastodon', placeholder: 'https://hachyderm.io/@you' },
  { value: 'bluesky', label: 'Bluesky', placeholder: 'https://bsky.app/profile/you.dev' },
  { value: 'website', label: 'Website', placeholder: 'https://you.dev' },
  { value: 'blog', label: 'Blog', placeholder: 'https://you.dev/blog' },
  { value: 'youtube', label: 'YouTube', placeholder: 'https://youtube.com/@you' },
  { value: 'other', label: 'Other', placeholder: 'https://' },
]

export const linkKindLabel = Object.fromEntries(linkKinds.map((k) => [k.value, k.label])) as Record<
  LinkKind,
  string
>

/** "https://github.com/ada/" -> "github.com/ada" for display. */
export function shortUrl(url: string) {
  return url
    .replace(/^https?:\/\/(www\.)?/, '')
    .replace(/[?#].*$/, '')
    .replace(/\/$/, '')
}
