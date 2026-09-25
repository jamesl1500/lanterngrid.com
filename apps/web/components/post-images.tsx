import { cn } from '@lanterngrid/ui'

import type { PostImage } from '@/lib/posts'

/** A post's images: one large, or a grid of up to four. Each opens full size. */
export function PostImages({ images }: { images: PostImage[] }) {
  if (images.length === 0) return null
  const single = images.length === 1
  return (
    <ul
      aria-label="Images"
      className={cn(
        'grid gap-1 border-2 border-line-strong bg-line-strong',
        !single && 'grid-cols-2',
      )}
    >
      {images.map((image, index) => (
        <li key={image.key} className={cn(images.length === 3 && index === 0 && 'row-span-2')}>
          <a href={image.url} target="_blank" rel="noopener" className="block size-full bg-sunk">
            {/* eslint-disable-next-line @next/next/no-img-element -- served from the bucket */}
            <img
              src={image.url}
              alt={image.alt}
              loading="lazy"
              className={cn(
                'size-full',
                single ? 'max-h-[32rem] object-contain' : 'aspect-square object-cover',
                images.length === 3 && index === 0 && 'aspect-auto',
              )}
            />
          </a>
        </li>
      ))}
    </ul>
  )
}
