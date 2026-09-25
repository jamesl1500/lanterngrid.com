import { highlight } from '@/lib/highlight'

import { CopyButton } from './copy-button'

/** A fenced code block: language label, copy button and highlighted code. */
export async function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const html = await highlight(code, lang)
  return (
    <figure className="code-block my-1 border-2 border-line-strong bg-sunk">
      <figcaption className="flex items-center justify-between border-b border-line px-3 py-1 font-mono text-[0.68rem] tracking-[0.08em] text-ink-3 uppercase">
        <span>{lang || 'code'}</span>
        <CopyButton text={code} className="uppercase hover:text-ink" />
      </figcaption>
      {/* Shiki escapes the code; the HTML is only its own spans. */}
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </figure>
  )
}
