import { isValidElement, type ComponentProps, type ReactElement, type ReactNode } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { remarkEntities, type Entities } from '@/lib/markdown/entities'

import { CodeBlock } from './code-block'

type CodeProps = { className?: string; children?: ReactNode }

function Pre({ children }: ComponentProps<'pre'>) {
  // react-markdown renders fenced code as <pre><code class="language-x">…</code></pre>.
  const code = isValidElement(children) ? (children as ReactElement<CodeProps>) : null
  const lang = code?.props.className?.match(/language-(\S+)/)?.[1]
  const text = String(code?.props.children ?? '').replace(/\n$/, '')
  return <CodeBlock code={text} lang={lang} />
}

function Anchor({ href = '', children }: ComponentProps<'a'>) {
  const internal = href.startsWith('/')
  return (
    <a
      href={href}
      {...(internal ? {} : { target: '_blank', rel: 'nofollow ugc noopener noreferrer' })}
    >
      {children}
    </a>
  )
}

// Posts can't embed images from anywhere yet (uploads come with comments and reactions);
// show the link instead so nothing loads from third parties.
function Image({ src, alt }: ComponentProps<'img'>) {
  return typeof src === 'string' ? <Anchor href={src}>{alt || src}</Anchor> : null
}

const components: Components = { pre: Pre, a: Anchor, img: Image }

/** A post body: GitHub-flavored Markdown with highlighted code and linked #tags and @people. */
export function Markdown({ source, entities }: { source: string; entities: Entities }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, [remarkEntities, entities]]}
        components={components}
        skipHtml
      >
        {source}
      </ReactMarkdown>
    </div>
  )
}
