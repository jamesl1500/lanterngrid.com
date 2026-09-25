import type { Schemas } from '@lanterngrid/api-client'

import type { Entities } from './markdown/entities'

export type Post = Schemas['PostOut']
export type PostPage = Schemas['PostPage']
export type PostImage = Schemas['PostImageOut']
export type Visibility = Schemas['PostCreate']['visibility']
export type Comment = Schemas['CommentOut']
export type ReactionKind = Schemas['ReactionCount']['kind']
export type ReactionCount = Schemas['ReactionCount']

export const MAX_POST_LENGTH = 5000
export const MAX_COMMENT_LENGTH = 2000
export const MAX_IMAGES = 4

export const reactionInfo: Record<ReactionKind, { emoji: string; label: string }> = {
  like: { emoji: '👍', label: 'Like' },
  ship: { emoji: '🚀', label: 'Ship it' },
  love: { emoji: '❤️', label: 'Love' },
  idea: { emoji: '💡', label: 'Insightful' },
  laugh: { emoji: '😄', label: 'Funny' },
  eyes: { emoji: '👀', label: 'Watching' },
}

/** Every reaction, in the order the API returns them. */
export const reactions = Object.entries(reactionInfo).map(([kind, info]) => ({
  kind: kind as ReactionKind,
  ...info,
}))

/** Add or remove the viewer's reaction locally, keeping the API's order. */
export function toggleReaction(counts: ReactionCount[], kind: ReactionKind): ReactionCount[] {
  const current = counts.find((r) => r.kind === kind)
  const next = current
    ? { kind, count: current.count + (current.mine ? -1 : 1), mine: !current.mine }
    : { kind, count: 1, mine: true }
  return reactions
    .map(({ kind: k }) => (k === kind ? next : counts.find((r) => r.kind === k)))
    .filter((r): r is ReactionCount => r !== undefined && r.count > 0)
}

export function postEntities(post: Pick<Post, 'tags' | 'mentions'>): Entities {
  return {
    tags: new Set(post.tags.map((t) => t.slug)),
    mentions: new Set(post.mentions.map((m) => m.toLowerCase())),
  }
}
