import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'

export const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 border-2 border-line-strong font-mono font-medium',
    'whitespace-nowrap transition-[transform,box-shadow] duration-100 select-none',
    'shadow-hard-sm hover:-translate-x-px hover:-translate-y-px hover:shadow-hard',
    'active:translate-x-0.5 active:translate-y-0.5 active:shadow-none',
    'disabled:pointer-events-none disabled:opacity-50',
  ],
  {
    variants: {
      variant: {
        primary: 'bg-ink text-ground',
        secondary: 'bg-surface text-ink',
        accent: 'bg-amber text-[#0c1017]',
        ghost:
          'border-transparent bg-transparent text-ink shadow-none hover:translate-0 hover:bg-sunk hover:shadow-none',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

export type ButtonProps = ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    /** Render the child element (e.g. a Next.js Link) with button styles. */
    asChild?: boolean
  }

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : 'button'
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />
}
