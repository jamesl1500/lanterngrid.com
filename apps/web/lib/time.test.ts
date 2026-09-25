import { timeAgo } from './time'

const now = new Date('2026-09-25T12:00:00Z')
const ago = (seconds: number) => new Date(now.getTime() - seconds * 1000)

describe('timeAgo', () => {
  it('says just now for the last minute', () => {
    expect(timeAgo(ago(20), now)).toBe('just now')
  })

  it('picks the largest whole unit', () => {
    expect(timeAgo(ago(5 * 60), now)).toBe('5 min. ago')
    expect(timeAgo(ago(3 * 3600), now)).toBe('3 hr. ago')
    expect(timeAgo(ago(24 * 3600), now)).toBe('yesterday')
    expect(timeAgo(ago(15 * 24 * 3600), now)).toBe('2 wk. ago')
  })
})
