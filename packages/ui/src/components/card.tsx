import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'

export type CardProps = ComponentProps<'div'> & {
  /** Lift the card with a hard shadow. Use for the one object that needs attention. */
  raised?: boolean
}

export function Card({ className, raised = false, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'bg-surface text-ink',
        raised ? 'border-2 border-line-strong shadow-hard' : 'border border-line',
        className,
      )}
      {...props}
    />
  )
}

export function CardHeader({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      className={cn('flex items-center gap-3 border-b border-line px-4 py-3', className)}
      {...props}
    />
  )
}

export function CardBody({ className, ...props }: ComponentProps<'div'>) {
  return <div className={cn('grid gap-3 px-4 py-3', className)} {...props} />
}

export function CardFooter({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      className={cn(
        'flex divide-x divide-line border-t border-line font-mono text-xs text-ink-2 *:flex-1 *:px-3 *:py-2 *:text-center',
        className,
      )}
      {...props}
    />
  )
}
