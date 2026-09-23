import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'
import { accentClasses, type Accent } from '../lib/kinds'

const sizes = { sm: 'size-7 text-xs', md: 'size-9 text-sm', lg: 'size-16 text-xl' } as const

export type AvatarProps = Omit<ComponentProps<'span'>, 'children'> & {
  name: string
  src?: string | null
  accent?: Accent
  size?: keyof typeof sizes
}

export function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  const first = parts[0]?.[0] ?? '?'
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase()
}

/** Square avatar. Falls back to initials on the user's accent color. */
export function Avatar({
  name,
  src,
  accent = 'violet',
  size = 'md',
  className,
  ...props
}: AvatarProps) {
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center justify-center overflow-hidden border-2 border-line-strong font-display font-bold text-[#0c1017]',
        accentClasses[accent].solid,
        sizes[size],
        className,
      )}
      {...props}
    >
      {src ? (
        // Plain img keeps the kit framework-agnostic; apps can pass an optimized URL.
        <img src={src} alt={name} className="size-full object-cover" />
      ) : (
        <span aria-label={name} role="img">
          {initials(name)}
        </span>
      )}
    </span>
  )
}
