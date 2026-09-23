import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'

const tones = {
  info: 'border-cyan bg-cyan-soft',
  success: 'border-lime bg-lime-soft',
  warning: 'border-amber bg-amber-soft',
  error: 'border-coral bg-coral-soft',
} as const

export type AlertProps = ComponentProps<'div'> & { tone?: keyof typeof tones }

export function Alert({ tone = 'info', className, ...props }: AlertProps) {
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={cn('border-l-4 px-4 py-3 text-sm text-ink', tones[tone], className)}
      {...props}
    />
  )
}
