import { retryDelay } from './realtime'

describe('retryDelay', () => {
  it('doubles up to 30 seconds', () => {
    const mid = () => 0.5
    expect([0, 1, 2, 3, 10].map((n) => retryDelay(n, mid))).toEqual([1000, 2000, 4000, 8000, 30000])
  })

  it('jitters by up to a fifth either way', () => {
    expect(retryDelay(0, () => 0)).toBe(800)
    expect(retryDelay(0, () => 1)).toBe(1200)
  })
})
