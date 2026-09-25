import { languageFromFilename, languageOptions } from './snippets'

describe('languageFromFilename', () => {
  it('knows common extensions', () => {
    expect(languageFromFilename('main.rs')).toBe('rust')
    expect(languageFromFilename(' App.TSX ')).toBe('tsx')
    expect(languageFromFilename('infra/main.tf')).toBe('hcl')
  })

  it('knows Dockerfiles', () => {
    expect(languageFromFilename('Dockerfile')).toBe('dockerfile')
    expect(languageFromFilename('api.Dockerfile')).toBe('dockerfile')
  })

  it('gives up on anything else', () => {
    expect(languageFromFilename('README')).toBeNull()
    expect(languageFromFilename('notes.weird')).toBeNull()
  })
})

describe('languageOptions', () => {
  it('puts plain text first, then sorts by name', () => {
    expect(languageOptions[0]).toBe('text')
    expect(languageOptions.slice(1, 3)).toEqual(['bash', 'c'])
  })
})
