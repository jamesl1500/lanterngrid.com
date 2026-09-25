'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { remarkEntities } from '@/lib/markdown/entities'
import { slugify } from '@/lib/tags'

const TAG = /(?<![\w#&/])#([A-Za-z][A-Za-z0-9_+#.-]*)/g
const MENTION = /(?<![\w@/.])@([A-Za-z0-9][A-Za-z0-9_-]*[A-Za-z0-9])/g

/**
 * The composer's preview. Links every #tag and @name as written (the saved post only links
 * people who exist), and shows code unhighlighted to keep the browser bundle small.
 */
export function MarkdownPreview({ source }: { source: string }) {
  const entities = {
    tags: new Set(
      [...source.matchAll(TAG)].map((m) => slugify((m[1] ?? '').replace(/[.-]+$/, ''))),
    ),
    mentions: new Set([...source.matchAll(MENTION)].map((m) => (m[1] ?? '').toLowerCase())),
  }
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, [remarkEntities, entities]]}
        components={{
          pre: ({ children }) => (
            <div className="code-block border-2 border-line-strong bg-sunk">
              <pre>{children}</pre>
            </div>
          ),
          a: ({ children, href }) => <a href={href}>{children}</a>,
          img: ({ alt, src }) => <a href={typeof src === 'string' ? src : undefined}>{alt}</a>,
        }}
        skipHtml
      >
        {source}
      </ReactMarkdown>
    </div>
  )
}
