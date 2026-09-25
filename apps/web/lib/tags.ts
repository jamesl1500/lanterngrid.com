import type { TagSuggestion } from '@lanterngrid/ui'

import { browserApi } from './api'

export const MAX_TAGS = 12

/** Tag suggestions for TagInput. Throws on failure; TagInput ignores errors. */
export async function suggestTags(q: string): Promise<TagSuggestion[]> {
  const { data } = await browserApi.GET('/v1/tags/suggest', { params: { query: { q } } })
  if (!data) throw new Error('No suggestions')
  return data
}
