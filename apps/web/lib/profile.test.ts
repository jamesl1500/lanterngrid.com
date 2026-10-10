import { moveRow, sectionRows, shownSections } from './profile'

describe('profile sections', () => {
  it('lists shown sections first, then the hidden ones', () => {
    expect(sectionRows(['posts', 'readme'])).toEqual([
      { section: 'posts', shown: true },
      { section: 'readme', shown: true },
      { section: 'pinned', shown: false },
      { section: 'friends', shown: false },
    ])
  })

  it('moves rows and saves only the shown ones, in order', () => {
    const rows = sectionRows(['readme', 'pinned', 'friends', 'posts'])
    const moved = moveRow(rows, 3, -1)
    expect(shownSections(moved)).toEqual(['readme', 'pinned', 'posts', 'friends'])
    expect(moveRow(rows, 0, -1)).toBe(rows)
    expect(moveRow(rows, 3, 1)).toBe(rows)
    const hidden = moved.map((r) => (r.section === 'pinned' ? { ...r, shown: false } : r))
    expect(shownSections(hidden)).toEqual(['readme', 'posts', 'friends'])
  })
})
