import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'

const control = [
  'w-full border-2 border-line-strong bg-surface px-3 text-ink placeholder:text-ink-3',
  'transition-shadow focus:shadow-hard-sm focus:outline-none focus-visible:outline-none',
  'disabled:cursor-not-allowed disabled:opacity-50',
  'aria-invalid:border-coral',
].join(' ')

export function Input({ className, ...props }: ComponentProps<'input'>) {
  return <input className={cn(control, 'h-10', className)} {...props} />
}

export function Textarea({ className, ...props }: ComponentProps<'textarea'>) {
  return <textarea className={cn(control, 'min-h-24 py-2', className)} {...props} />
}

/** Native select, restyled. Native keeps keyboard, mobile pickers and autofill for free. */
export function Select({ className, children, ...props }: ComponentProps<'select'>) {
  return (
    <span className={cn('relative block', className)}>
      <select className={cn(control, 'h-10 cursor-pointer appearance-none pr-9')} {...props}>
        {children}
      </select>
      <span
        aria-hidden
        className="pointer-events-none absolute inset-y-0 right-3 flex items-center font-mono text-xs text-ink-3"
      >
        ▾
      </span>
    </span>
  )
}
