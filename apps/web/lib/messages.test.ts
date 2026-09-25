import { conversationName, mergeMessages, seenBy, type ChatMessage, type Member } from './messages'

const ada = {
  id: 'u-ada',
  username: 'ada',
  display_name: 'Ada',
  headline: null,
  avatar_url: null,
  accent_color: 'cyan' as const,
}
const ben = { ...ada, id: 'u-ben', username: 'ben', display_name: 'Ben' }

function msg(id: string, client_id: string, extra: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id,
    client_id,
    conversation_id: 'c1',
    sender: ada,
    body: client_id,
    created_at: '2026-09-25T12:00:00Z',
    ...extra,
  }
}

describe('mergeMessages', () => {
  it('orders by id and drops duplicates', () => {
    const merged = mergeMessages([msg('01b', 'b')], [msg('01a', 'a'), msg('01b', 'b')])
    expect(merged.map((m) => m.client_id)).toEqual(['a', 'b'])
  })

  it('replaces a pending message once it is sent, and keeps pending ones last', () => {
    const pending = msg('tmp', 'x', { status: 'sending', created_at: '2026-09-25T12:05:00Z' })
    const other = msg('01c', 'y', { sender: ben })
    expect(mergeMessages([pending], [other]).map((m) => m.client_id)).toEqual(['y', 'x'])
    const sent = mergeMessages([pending, other], [msg('01d', 'x')])
    expect(sent.map((m) => [m.client_id, m.status])).toEqual([
      ['y', undefined],
      ['x', undefined],
    ])
    // A late pending copy doesn't undo the sent one.
    expect(mergeMessages(sent, [pending]).find((m) => m.client_id === 'x')?.status).toBeUndefined()
  })
})

describe('conversationName', () => {
  const members: Member[] = [
    { user: ada, role: 'member', last_read_message_id: null },
    { user: ben, role: 'member', last_read_message_id: null },
  ]
  const base = {
    id: 'c1',
    kind: 'dm' as const,
    title: null,
    members,
    last_message: null,
    unread_count: 0,
    last_message_at: '',
    created_at: '',
  }

  it('names a DM after the other person and a group by its title', () => {
    expect(conversationName(base, 'u-ada')).toBe('Ben')
    expect(conversationName({ ...base, kind: 'group', title: 'Crew' }, 'u-ada')).toBe('Crew')
  })
})

describe('seenBy', () => {
  it('lists people whose read marker reached the message', () => {
    const members: Member[] = [
      { user: ada, role: 'owner', last_read_message_id: '01c' },
      { user: ben, role: 'member', last_read_message_id: '01b' },
    ]
    expect(seenBy(members, '01b', 'u-ada').map((m) => m.user.username)).toEqual(['ben'])
    expect(seenBy(members, '01c', 'u-ada')).toEqual([])
  })
})
