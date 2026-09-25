import { shortUrl } from './links'
import { linksSchema } from './validation'

describe('shortUrl', () => {
  it('drops the scheme, www, query and trailing slash', () => {
    expect(shortUrl('https://www.github.com/ada/?tab=repos')).toBe('github.com/ada')
    expect(shortUrl('http://hachyderm.io/@ada')).toBe('hachyderm.io/@ada')
  })
})

describe('linksSchema', () => {
  it('needs a full http(s) link in every row', () => {
    const result = linksSchema.safeParse({
      links: [
        { kind: 'github', url: 'https://github.com/ada' },
        { kind: 'blog', url: '' },
        { kind: 'x', url: 'javascript:alert(1)' },
      ],
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues.map((i) => i.path.join('.'))).toEqual([
      'links.1.url',
      'links.2.url',
    ])
  })

  it('allows at most eight links', () => {
    const links = Array.from({ length: 9 }, (_, i) => ({
      kind: 'other' as const,
      url: `https://example.com/${i}`,
    }))
    expect(linksSchema.safeParse({ links }).success).toBe(false)
  })
})
