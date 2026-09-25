import { cn } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'

import { highlight } from '@/lib/highlight'

import { CopyButton } from './copy-button'

type Props = {
  code: string
  lang?: string
  /** Shown instead of the language, e.g. a filename. */
  label?: string
  lineNumbers?: boolean
  /** Show only this many lines, with a link to the rest. */
  maxLines?: number
  moreHref?: Route
}

/** A block of code: label, copy button and highlighted code. */
export async function CodeBlock({ code, lang, label, lineNumbers, maxLines, moreHref }: Props) {
  const lines = code.split('\n')
  const hidden = maxLines && lines.length > maxLines ? lines.length - maxLines : 0
  const html = await highlight(hidden ? lines.slice(0, maxLines).join('\n') : code, lang)
  return (
    <figure
      className={cn(
        'code-block my-1 border-2 border-line-strong bg-sunk',
        lineNumbers && 'code-block--numbered',
      )}
    >
      <figcaption className="flex items-center justify-between gap-3 border-b border-line px-3 py-1 font-mono text-[0.68rem] tracking-[0.08em] text-ink-3">
        <span className={cn('truncate', !label && 'uppercase')}>{label || lang || 'code'}</span>
        <CopyButton text={code} className="uppercase hover:text-ink" />
      </figcaption>
      {/* Shiki escapes the code; the HTML is only its own spans. */}
      <div dangerouslySetInnerHTML={{ __html: html }} />
      {hidden ? (
        <div className="border-t border-line px-3 py-1.5 font-mono text-xs">
          {moreHref ? (
            <Link href={moreHref} className="text-violet hover:underline">
              {hidden} more {hidden === 1 ? 'line' : 'lines'} →
            </Link>
          ) : (
            <span className="text-ink-3">{hidden} more lines</span>
          )}
        </div>
      ) : null}
    </figure>
  )
}
