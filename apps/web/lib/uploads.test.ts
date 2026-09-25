import { imageProblem } from './uploads'

const MB = 1024 * 1024

describe('imageProblem', () => {
  it('accepts supported images within the limit', () => {
    expect(imageProblem('avatar', { type: 'image/png', size: 2 * MB })).toBeNull()
    expect(imageProblem('banner', { type: 'image/webp', size: 5 * MB })).toBeNull()
  })

  it('rejects other file types', () => {
    expect(imageProblem('avatar', { type: 'image/svg+xml', size: 100 })).toBe(
      'Use a PNG, JPEG, WebP or GIF image.',
    )
  })

  it('rejects files over the limit for their kind', () => {
    expect(imageProblem('avatar', { type: 'image/png', size: 2 * MB + 1 })).toBe(
      'Avatars can be up to 2 MB.',
    )
    expect(imageProblem('banner', { type: 'image/gif', size: 5 * MB + 1 })).toBe(
      'Banners can be up to 5 MB.',
    )
    expect(imageProblem('post', { type: 'image/jpeg', size: 5 * MB + 1 })).toBe(
      'Images can be up to 5 MB.',
    )
  })
})
