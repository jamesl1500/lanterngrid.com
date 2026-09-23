import { profileSchema, username } from './validation'

describe('username', () => {
  it.each(['ada', 'ada_park-99', 'A1b'])('accepts %s', (name) => {
    expect(username.safeParse(name).success).toBe(true)
  })

  it.each(['ab', '-ada', 'ada-', 'ada park', 'a'.repeat(31)])('rejects %s', (name) => {
    expect(username.safeParse(name).success).toBe(false)
  })
})

describe('profileSchema', () => {
  const base = {
    display_name: 'Ada',
    headline: '',
    bio: '',
    location: '',
    website: '',
    accent_color: 'violet',
  }

  it('allows an empty website but not a non-link', () => {
    expect(profileSchema.safeParse(base).success).toBe(true)
    expect(profileSchema.safeParse({ ...base, website: 'https://ada.dev' }).success).toBe(true)
    expect(profileSchema.safeParse({ ...base, website: 'javascript:alert(1)' }).success).toBe(false)
  })
})
