import { accents } from '@lanterngrid/ui'

import { formatCount, languageAccent } from './repos'

describe('formatCount', () => {
  it('keeps small numbers and shortens big ones', () => {
    expect(formatCount(0)).toBe('0')
    expect(formatCount(999)).toBe('999')
    expect(formatCount(1234)).toBe('1.2K')
    expect(formatCount(34_000)).toBe('34K')
    expect(formatCount(2_500_000)).toBe('2.5M')
  })
})

describe('languageAccent', () => {
  it('is one of the accents and ignores case', () => {
    expect(accents).toContain(languageAccent('Rust'))
    expect(languageAccent('TypeScript')).toBe(languageAccent('typescript'))
  })
})
