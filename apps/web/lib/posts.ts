import type { Schemas } from '@lanterngrid/api-client'

import type { Entities } from './markdown/entities'

export type Post = Schemas['PostOut']
export type PostPage = Schemas['PostPage']
export type Visibility = Schemas['PostCreate']['visibility']

export const MAX_POST_LENGTH = 5000

export function postEntities(post: Pick<Post, 'tags' | 'mentions'>): Entities {
  return {
    tags: new Set(post.tags.map((t) => t.slug)),
    mentions: new Set(post.mentions.map((m) => m.toLowerCase())),
  }
}
