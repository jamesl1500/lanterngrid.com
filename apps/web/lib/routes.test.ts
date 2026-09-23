import { githubStartUrl, homeFor, safeNext } from './routes'

describe('safeNext', () => {
  it.each(['/u/ada', '/settings/profile?tab=1'])('keeps %s', (path) => {
    expect(safeNext(path)).toBe(path)
  })

  it.each(['https://evil.example', '//evil.example', '/\\evil.example', '', null])(
    'drops %s',
    (path) => {
      expect(safeNext(path)).toBeNull()
    },
  )
})

describe('homeFor', () => {
  it('sends people without a username to onboarding', () => {
    expect(homeFor({ username: null }, '/u/ben')).toBe('/onboarding')
  })

  it('prefers a safe next path, else the profile', () => {
    expect(homeFor({ username: 'ada' }, '/u/ben')).toBe('/u/ben')
    expect(homeFor({ username: 'ada' }, '//evil')).toBe('/u/ada')
  })
})

describe('githubStartUrl', () => {
  it('passes next through encoded', () => {
    expect(githubStartUrl('/u/ben')).toBe('/api/v1/auth/github/start?next=%2Fu%2Fben')
    expect(githubStartUrl()).toBe('/api/v1/auth/github/start')
  })
})
