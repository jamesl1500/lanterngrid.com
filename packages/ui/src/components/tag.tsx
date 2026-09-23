import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'
import { accentClasses, type Accent } from '../lib/kinds'

export type TagProps = ComponentProps<'span'> & {
  /** The tag's slug, without the leading #. */
  name: string
  accent?: Accent
}

export function Tag({ name, accent = 'cyan', className, ...props }: TagProps) {
  const c = accentClasses[accent]
  return (
    <span
      className={cn(
        'inline-flex border px-1.5 font-mono text-xs',
        c.soft,
        c.text,
        c.border,
        className,
      )}
      {...props}
    >
      #{name}
    </span>
  )
}
