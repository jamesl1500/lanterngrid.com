import type { Schemas } from '@lanterngrid/api-client'

import { browserApi } from './api'

export const MAX_TAGS = 12

/** Tag suggestions for TagInput. Throws on failure; TagInput ignores errors. */
export async function suggestTags(q: string): Promise<Schemas['TagOut'][]> {
  const { data } = await browserApi.GET('/v1/tags/suggest', { params: { query: { q } } })
  if (!data) throw new Error('No suggestions')
  return data
}

const SPELLED_OUT: [string, string][] = [
  ['#', 'sharp'],
  ['+', 'p'],
]

/**
 * Same rules as the API's slugify(): "C++" -> "cpp", ".NET" -> "dotnet", "Node.js" -> "node.js".
 */
export function slugify(name: string) {
  let slug = name.trim().toLowerCase()
  for (const [char, word] of SPELLED_OUT) slug = slug.replaceAll(char, word)
  if (slug.startsWith('.')) slug = 'dot' + slug.slice(1)
  slug = slug.replace(/[^a-z0-9.-]+/g, '-').replace(/-{2,}/g, '-')
  return slug.slice(0, 32).replace(/^[-.]+|[-.]+$/g, '')
}
