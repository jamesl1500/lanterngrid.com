import type { Schemas } from '@lanterngrid/api-client'

import type { serverApi } from './api'
import type { Person } from './people'

export type Conversation = Schemas['ConversationOut']
export type Message = Schemas['MessageOut']
export type Member = Schemas['MemberOut']

export const MAX_MESSAGE_LENGTH = 4000
/** Everyone in a group, you included. Matches `MAX_GROUP_SIZE` in messaging/schemas.py. */
export const MAX_GROUP_SIZE = 20
export const MAX_GROUP_TITLE = 80

/** A message on screen: sent, still sending, or failed and waiting for a retry. */
export type ChatMessage = Message & { status?: 'sending' | 'failed' }

/**
 * Message ids are UUIDv7, so comparing them as strings compares when they were sent.
 * Pending messages have no real id yet and sort last, in the order they were written.
 */
function sortKey(m: ChatMessage) {
  return m.status ? `~${m.created_at}` : m.id
}

/** Add incoming messages, replacing pending ones with the same client_id, oldest first. */
export function mergeMessages(current: ChatMessage[], incoming: ChatMessage[]): ChatMessage[] {
  const byKey = new Map<string, ChatMessage>()
  for (const m of [...current, ...incoming]) {
    const key = `${m.sender?.id ?? ''}:${m.client_id}`
    const existing = byKey.get(key)
    // A sent message wins over its pending copy.
    if (!existing || existing.status || !m.status) byKey.set(key, m)
  }
  // Plain code-unit order: localeCompare would ignore the '~' that puts pending ones last.
  return [...byKey.values()].sort((a, b) => {
    const [x, y] = [sortKey(a), sortKey(b)]
    return x < y ? -1 : x > y ? 1 : 0
  })
}

/** A group's title, or the other people's names. */
export function conversationName(conversation: Conversation, meId: string) {
  if (conversation.title) return conversation.title
  const others = conversation.members.filter((m) => m.user.id !== meId)
  if (others.length === 0) return 'Just you'
  return others.map((m) => m.user.display_name).join(', ')
}

/** The other people, for avatars. */
export function others(conversation: Conversation, meId: string) {
  return conversation.members.filter((m) => m.user.id !== meId).map((m) => m.user)
}

/** Who has read up to `messageId`, not counting its sender. */
export function seenBy(members: Member[], messageId: string, senderId: string) {
  return members.filter(
    (m) =>
      m.user.id !== senderId &&
      m.last_read_message_id !== null &&
      m.last_read_message_id >= messageId,
  )
}

type Api = ReturnType<typeof serverApi>

/** Every friend, for picking who to message. Pages through the list, stopping at 500. */
export async function allFriends(api: Api, username: string): Promise<Person[]> {
  const friends: Person[] = []
  let cursor: string | undefined
  do {
    const { data } = await api.GET('/v1/users/{username}/friends', {
      params: { path: { username }, query: { cursor, limit: 50 } },
      cache: 'no-store',
    })
    if (!data) throw new Error('Could not load friends.')
    friends.push(...data.items)
    cursor = data.next_cursor ?? undefined
  } while (cursor && friends.length < 500)
  return friends.sort((a, b) => a.display_name.localeCompare(b.display_name))
}
