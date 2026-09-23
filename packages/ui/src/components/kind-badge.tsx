import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'
import { accentClasses, kindAccent, type ContentKind } from '../lib/kinds'

export type KindBadgeProps = ComponentProps<'span'> & { kind: ContentKind }

export function KindBadge({ kind, className, ...props }: KindBadgeProps) {
  const c = accentClasses[kindAccent[kind]]
  return (
    <span
      className={cn(
        'inline-flex border px-1.5 py-px font-mono text-[0.68rem] tracking-[0.08em] uppercase',
        c.soft,
        c.text,
        c.border,
        className,
      )}
      {...props}
    >
      {kind}
    </span>
  )
}
