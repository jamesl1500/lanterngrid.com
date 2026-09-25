import type { Root } from 'mdast'

import { slugify } from '../tags'
import { remarkEntities, splitText } from './entities'

const entities = { tags: new Set(['rust', 'cpp', 'node.js']), mentions: new Set(['ben']) }

describe('splitText', () => {
  it('links known tags and mentions, leaving the rest as text', () => {
    expect(splitText('I like #Rust and #go, ask @Ben or @nobody.', entities)).toEqual([
      { type: 'text', value: 'I like ' },
      { type: 'link', url: '/tags/rust', children: [{ type: 'text', value: '#Rust' }] },
      { type: 'text', value: ' and #go, ask ' },
      { type: 'link', url: '/u/Ben', children: [{ type: 'text', value: '@Ben' }] },
      { type: 'text', value: ' or @nobody.' },
    ])
  })

  it('keeps sentence punctuation out of the tag', () => {
    expect(splitText('#node.js.', entities)).toEqual([
      { type: 'link', url: '/tags/node.js', children: [{ type: 'text', value: '#node.js' }] },
      { type: 'text', value: '.' },
    ])
  })

  it('ignores emails and issue numbers', () => {
    const text = 'mail ben@example.com about #42'
    expect(splitText(text, entities)).toEqual([{ type: 'text', value: text }])
  })
})

describe('remarkEntities', () => {
  it('skips code and existing links', () => {
    const tree: Root = {
      type: 'root',
      children: [
        {
          type: 'paragraph',
          children: [
            { type: 'inlineCode', value: '#rust' },
            { type: 'link', url: 'https://x.dev', children: [{ type: 'text', value: '@ben' }] },
            { type: 'text', value: ' #C++' },
          ],
        },
        { type: 'code', lang: 'rust', value: '// #rust @ben' },
      ],
    }
    remarkEntities(entities)(tree)
    const paragraph = tree.children[0]
    expect(paragraph?.type === 'paragraph' && paragraph.children.map((c) => c.type)).toEqual([
      'inlineCode',
      'link',
      'text',
      'link',
    ])
    expect(tree.children[1]).toEqual({ type: 'code', lang: 'rust', value: '// #rust @ben' })
  })
})

describe('slugify', () => {
  it.each([
    ['TypeScript', 'typescript'],
    ['C++', 'cpp'],
    ['C#', 'csharp'],
    ['.NET', 'dotnet'],
    ['Node.js', 'node.js'],
    ['  Machine   learning ', 'machine-learning'],
    ['!!!', ''],
  ])('%s -> %s', (name, slug) => {
    expect(slugify(name)).toBe(slug)
  })
})
