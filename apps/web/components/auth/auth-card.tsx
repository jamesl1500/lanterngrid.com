import { Card } from '@lanterngrid/ui'
import type { ReactNode } from 'react'

export function AuthCard({
  eyebrow,
  title,
  children,
  footer,
}: {
  eyebrow: string
  title: string
  children: ReactNode
  footer?: ReactNode
}) {
  return (
    <main className="mx-auto grid w-full max-w-md gap-5 px-4 py-12">
      <Card raised className="grid gap-6 p-6 sm:p-8">
        <header className="grid gap-2">
          <span className="label">{eyebrow}</span>
          <h1 className="text-3xl font-bold">{title}</h1>
        </header>
        {children}
      </Card>
      {footer ? <div className="text-center text-sm text-ink-2">{footer}</div> : null}
    </main>
  )
}

export function OrDivider() {
  return (
    <div className="flex items-center gap-3 font-mono text-xs text-ink-3 uppercase">
      <span className="h-px flex-1 bg-line" />
      or
      <span className="h-px flex-1 bg-line" />
    </div>
  )
}
