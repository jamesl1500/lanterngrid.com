import { toggleReaction, type ReactionCount } from './posts'

describe('toggleReaction', () => {
  const counts: ReactionCount[] = [
    { kind: 'like', count: 2, mine: false },
    { kind: 'eyes', count: 1, mine: true },
  ]

  it('adds a reaction in order', () => {
    expect(toggleReaction(counts, 'ship')).toEqual([
      { kind: 'like', count: 2, mine: false },
      { kind: 'ship', count: 1, mine: true },
      { kind: 'eyes', count: 1, mine: true },
    ])
  })

  it('joins an existing reaction', () => {
    expect(toggleReaction(counts, 'like')[0]).toEqual({ kind: 'like', count: 3, mine: true })
  })

  it('drops a reaction nobody has left', () => {
    expect(toggleReaction(counts, 'eyes')).toEqual([{ kind: 'like', count: 2, mine: false }])
  })
})
