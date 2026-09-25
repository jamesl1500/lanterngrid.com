import type { Schemas } from '@lanterngrid/api-client'
import { accents, type Accent } from '@lanterngrid/ui'

export type Repo = Schemas['RepoOut']
export type RepoPage = Schemas['RepoPage']

const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 })

/** 999, 1.2K, 34K: short enough for a stats row. */
export function formatCount(n: number) {
  return n < 1000 ? String(n) : compact.format(n)
}

/** A language keeps the same accent everywhere, so a swatch reads at a glance. */
export function languageAccent(language: string): Accent {
  let hash = 0
  for (const char of language.toLowerCase()) hash = (hash * 31 + char.charCodeAt(0)) >>> 0
  return accents[hash % accents.length] ?? 'lime'
}
