'use client'

import { useId, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

import { cn } from '../lib/cn'
import type { Accent } from '../lib/kinds'

// Full class names so Tailwind's scanner can see them.
const topEdge: Record<Accent, string> = {
  cyan: 'border-t-cyan',
  violet: 'border-t-violet',
  lime: 'border-t-lime',
  amber: 'border-t-amber',
  magenta: 'border-t-magenta',
  coral: 'border-t-coral',
}

export type DialogProps = {
  open: boolean
  /** Called on Escape, a click outside, or a close button inside calling it. */
  onClose: () => void
  title: string
  /** The strip along the top. */
  accent?: Accent
  className?: string
  children: ReactNode
}

/**
 * A modal dialog on the native <dialog> element, so focus trapping, Escape and the backdrop
 * come from the browser. It renders into <body>, which keeps it working when opened from
 * inside a menu that closes.
 */
export function Dialog({
  open,
  onClose,
  title,
  accent = 'cyan',
  className,
  children,
}: DialogProps) {
  const titleId = useId()
  if (!open) return null
  return createPortal(
    <dialog
      ref={(el) => {
        if (el && !el.open) el.showModal()
      }}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(e) => {
        // A click on the backdrop lands on the dialog itself, outside its content.
        if (e.target === e.currentTarget) onClose()
      }}
      className={cn(
        'm-auto w-[calc(100%-2rem)] max-w-lg border-2 border-t-4 border-line-strong bg-surface p-0 text-ink shadow-hard backdrop:bg-ground/70',
        topEdge[accent],
        className,
      )}
    >
      <div className="grid gap-4 p-5">
        <h2 id={titleId} className="font-display text-xl font-bold">
          {title}
        </h2>
        {children}
      </div>
    </dialog>,
    document.body,
  )
}
