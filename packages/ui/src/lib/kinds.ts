/** Every kind of content has its own accent so the feed reads at a glance. */
export const contentKinds = [
  'update',
  'snippet',
  'repo',
  'achievement',
  'message',
  'alert',
] as const
export type ContentKind = (typeof contentKinds)[number]

export const accents = ['cyan', 'violet', 'lime', 'amber', 'magenta', 'coral'] as const
export type Accent = (typeof accents)[number]

export const kindAccent: Record<ContentKind, Accent> = {
  update: 'cyan',
  snippet: 'violet',
  repo: 'lime',
  achievement: 'amber',
  message: 'magenta',
  alert: 'coral',
}

// Full class names so Tailwind's scanner can see them.
export const accentClasses: Record<
  Accent,
  { solid: string; soft: string; text: string; border: string }
> = {
  cyan: { solid: 'bg-cyan', soft: 'bg-cyan-soft', text: 'text-cyan', border: 'border-cyan' },
  violet: {
    solid: 'bg-violet',
    soft: 'bg-violet-soft',
    text: 'text-violet',
    border: 'border-violet',
  },
  lime: { solid: 'bg-lime', soft: 'bg-lime-soft', text: 'text-lime', border: 'border-lime' },
  amber: { solid: 'bg-amber', soft: 'bg-amber-soft', text: 'text-amber', border: 'border-amber' },
  magenta: {
    solid: 'bg-magenta',
    soft: 'bg-magenta-soft',
    text: 'text-magenta',
    border: 'border-magenta',
  },
  coral: { solid: 'bg-coral', soft: 'bg-coral-soft', text: 'text-coral', border: 'border-coral' },
}
