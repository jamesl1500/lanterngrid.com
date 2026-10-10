import type { Schemas } from '@lanterngrid/api-client'

export type ProfileSection = Schemas['PublicProfile']['sections'][number]

/** Every section a profile page can show, in the default order. */
export const PROFILE_SECTIONS: readonly ProfileSection[] = ['readme', 'pinned', 'friends', 'posts']

export const sectionLabels: Record<ProfileSection, string> = {
  readme: 'README',
  pinned: 'Pinned',
  friends: 'Friends',
  posts: 'Posts',
}

export const MAX_README_LENGTH = 10_000

/** A section with whether it's shown, for the settings list: shown ones first, in order. */
export type SectionRow = { section: ProfileSection; shown: boolean }

export function sectionRows(shown: readonly ProfileSection[]): SectionRow[] {
  const hidden = PROFILE_SECTIONS.filter((s) => !shown.includes(s))
  return [
    ...shown.map((section) => ({ section, shown: true })),
    ...hidden.map((section) => ({ section, shown: false })),
  ]
}

/** Move a row up (-1) or down (+1), staying within the list. */
export function moveRow(rows: SectionRow[], index: number, by: -1 | 1): SectionRow[] {
  const target = index + by
  if (target < 0 || target >= rows.length) return rows
  const next = [...rows]
  const [row] = next.splice(index, 1)
  if (row) next.splice(target, 0, row)
  return next
}

/** What to save: the shown sections, in order. */
export function shownSections(rows: SectionRow[]): ProfileSection[] {
  return rows.filter((r) => r.shown).map((r) => r.section)
}
