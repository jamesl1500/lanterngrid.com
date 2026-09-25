import type { Schemas } from '@lanterngrid/api-client'

import { browserApi } from './api'

export type Person = Schemas['UserSummary']

/** People search for the search box. Throws on failure so callers can keep old results. */
export async function searchPeople(q: string): Promise<Person[]> {
  const { data } = await browserApi.GET('/v1/people/search', { params: { query: { q } } })
  if (!data) throw new Error('Search failed')
  return data
}
