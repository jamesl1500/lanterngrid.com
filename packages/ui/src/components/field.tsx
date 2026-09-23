import type { ComponentProps, ReactNode } from 'react'

import { cn } from '../lib/cn'
import { Input, Select, Textarea } from './input'

export type FieldProps = {
  /** id of the control inside, so the label and messages point at it. */
  id: string
  label: string
  hint?: ReactNode
  error?: string
  className?: string
  children: ReactNode
}

/**
 * Label, control, hint and error stacked together. Give the control
 * `aria-describedby={describedBy(id, …)}` and `aria-invalid` so screen readers read them.
 */
export function Field({ id, label, hint, error, className, children }: FieldProps) {
  return (
    <div className={cn('grid gap-1.5', className)}>
      <label htmlFor={id} className="font-mono text-xs tracking-[0.08em] text-ink-2 uppercase">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="text-sm text-coral">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-sm text-ink-3">
          {hint}
        </p>
      ) : null}
    </div>
  )
}

export function describedBy(id: string, { error, hint }: { error?: string; hint?: unknown }) {
  if (error) return `${id}-error`
  if (hint) return `${id}-hint`
  return undefined
}

export type TextFieldProps = ComponentProps<'input'> & {
  id: string
  label: string
  hint?: ReactNode
  error?: string
}

/** A labelled text input with its hint and error wired up for screen readers. */
export function TextField({ id, label, hint, error, className, ...props }: TextFieldProps) {
  return (
    <Field id={id} label={label} hint={hint} error={error} className={className}>
      <Input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, { error, hint })}
        {...props}
      />
    </Field>
  )
}

export type TextAreaFieldProps = ComponentProps<'textarea'> & {
  id: string
  label: string
  hint?: ReactNode
  error?: string
}

export function TextAreaField({ id, label, hint, error, className, ...props }: TextAreaFieldProps) {
  return (
    <Field id={id} label={label} hint={hint} error={error} className={className}>
      <Textarea
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, { error, hint })}
        {...props}
      />
    </Field>
  )
}

export type SelectFieldProps = ComponentProps<'select'> & {
  id: string
  label: string
  hint?: ReactNode
  error?: string
}

export function SelectField({ id, label, hint, error, className, ...props }: SelectFieldProps) {
  return (
    <Field id={id} label={label} hint={hint} error={error} className={className}>
      <Select
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, { error, hint })}
        {...props}
      />
    </Field>
  )
}
