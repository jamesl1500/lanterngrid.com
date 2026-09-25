import type { Link, Parent, PhrasingContent, Root, Text } from 'mdast'

import { slugify } from '../tags'

// Same patterns as the API (app/modules/posts/text.py), so what's linked is what was saved.
const ENTITY =
  /(?<![\w#&/])#([A-Za-z][A-Za-z0-9_+#.-]*)|(?<![\w@/.])@([A-Za-z0-9][A-Za-z0-9_-]*[A-Za-z0-9])/g

export type Entities = {
  /** Slugs of the post's tags. */
  tags: ReadonlySet<string>
  /** Lowercased usernames the post mentions. */
  mentions: ReadonlySet<string>
}

function link(url: string, value: string): Link {
  return { type: 'link', url, children: [{ type: 'text', value }] }
}

/** Split one text node into text and links for the #tags and @mentions the post really has. */
export function splitText(value: string, entities: Entities): PhrasingContent[] {
  const out: PhrasingContent[] = []
  let last = 0
  for (const match of value.matchAll(ENTITY)) {
    const [whole, tag, mention] = match
    let node: Link | null = null
    let length = whole.length
    if (tag !== undefined) {
      const name = tag.replace(/[.-]+$/, '')
      length = name.length + 1
      const slug = slugify(name)
      if (entities.tags.has(slug)) node = link(`/tags/${encodeURIComponent(slug)}`, `#${name}`)
    } else if (mention !== undefined && entities.mentions.has(mention.toLowerCase())) {
      node = link(`/u/${mention}`, whole)
    }
    if (!node) continue
    if (match.index > last) out.push({ type: 'text', value: value.slice(last, match.index) })
    out.push(node)
    last = match.index + length
  }
  if (last === 0) return [{ type: 'text', value }]
  if (last < value.length) out.push({ type: 'text', value: value.slice(last) })
  return out
}

function walk(node: Parent, entities: Entities) {
  if (node.type === 'link' || node.type === 'linkReference') return
  const children: typeof node.children = []
  for (const child of node.children) {
    if (child.type === 'text') {
      children.push(...splitText((child as Text).value, entities))
    } else {
      if ('children' in child) walk(child as Parent, entities)
      children.push(child)
    }
  }
  node.children = children
}

/** Remark plugin: turn #tags and @mentions into links. Code is left alone. */
export function remarkEntities(entities: Entities) {
  return (tree: Root) => walk(tree, entities)
}
