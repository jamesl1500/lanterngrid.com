import { activeToken, insertAt, tagText } from './composer'

describe('activeToken', () => {
  it('finds a mention or tag being typed', () => {
    expect(activeToken('hi @ad', 6)).toEqual({ trigger: '@', query: 'ad', start: 3, end: 6 })
    expect(activeToken('#ru', 3)).toEqual({ trigger: '#', query: 'ru', start: 0, end: 3 })
    expect(activeToken('(#go', 4)).toEqual({ trigger: '#', query: 'go', start: 1, end: 4 })
  })

  it('ignores emails, finished words and text after the caret', () => {
    expect(activeToken('ada@exa', 7)).toBeNull()
    expect(activeToken('hi @ada ', 8)).toBeNull()
    expect(activeToken('hi @ada', 2)).toBeNull()
  })
})

describe('insertAt', () => {
  it('replaces the token and puts the caret after a space', () => {
    expect(insertAt('hi @ad there', { start: 3, end: 6 }, '@adapark')).toEqual({
      text: 'hi @adapark there',
      caret: 12,
    })
    expect(insertAt('#ru', { start: 0, end: 3 }, '#Rust')).toEqual({ text: '#Rust ', caret: 6 })
  })
})

describe('tagText', () => {
  it('uses the slug when the name has spaces', () => {
    expect(tagText({ name: 'Rust', slug: 'rust' })).toBe('#Rust')
    expect(tagText({ name: 'Tailwind CSS', slug: 'tailwind-css' })).toBe('#tailwind-css')
  })
})
