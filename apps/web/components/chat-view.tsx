'use client'

import { Alert, Avatar, Button, cn, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import {
  MAX_MESSAGE_LENGTH,
  mergeMessages,
  seenBy,
  type ChatMessage,
  type Conversation,
  type Member,
  type Message,
} from '@/lib/messages'
import { realtime } from '@/lib/realtime'
import type { Me } from '@/lib/session'

type Props = {
  conversation: Conversation
  messages: Message[]
  olderCursor: string | null
  me: Pick<Me, 'id' | 'username' | 'display_name' | 'avatar_url' | 'accent_color'>
}

// Messages from one person this close together share a header.
const GROUP_GAP_MS = 5 * 60_000
const clock = new Intl.DateTimeFormat('en', { hour: 'numeric', minute: '2-digit' })

/** A live conversation: history, new messages over the socket, read receipts and sending. */
export function ChatView({
  conversation,
  messages: initial,
  olderCursor: initialCursor,
  me,
}: Props) {
  const router = useRouter()
  const id = conversation.id
  const [messages, setMessages] = useState<ChatMessage[]>(initial)
  const [members, setMembers] = useState<Member[]>(conversation.members)
  // People joined or left and the page refreshed: take the new list.
  const [shownMembers, setShownMembers] = useState(conversation.members)
  if (shownMembers !== conversation.members) {
    setShownMembers(conversation.members)
    setMembers(conversation.members)
  }
  const [olderCursor, setOlderCursor] = useState(initialCursor)
  const [loadingOlder, setLoadingOlder] = useState(false)
  const [body, setBody] = useState('')
  const [error, setError] = useState<string | null>(null)
  const list = useRef<HTMLOListElement>(null)
  // Whether to stick to the bottom when messages arrive (true unless scrolled up).
  const pinned = useRef(true)
  // Scroll height before older messages were added above, to keep the view still.
  const heightBeforeOlder = useRef<number | null>(null)

  const lastSentId = useCallback(
    (all: ChatMessage[]) => all.findLast((m) => !m.status)?.id ?? null,
    [],
  )

  // The newest message this tab has told the API it read.
  const reported = useRef(
    conversation.members.find((m) => m.user.id === me.id)?.last_read_message_id ?? null,
  )

  const markRead = useCallback(
    async (all: ChatMessage[]) => {
      const last = lastSentId(all)
      if (!last || document.visibilityState !== 'visible') return
      if (reported.current && reported.current >= last) return
      reported.current = last
      await browserApi.POST('/v1/conversations/{conversation_id}/read', {
        params: { path: { conversation_id: id } },
        body: { message_id: last },
      })
    },
    [id, lastSentId],
  )

  const catchUp = useCallback(async () => {
    const after = lastSentId(messages)
    const { data } = await browserApi.GET('/v1/conversations/{conversation_id}/messages', {
      params: { path: { conversation_id: id }, query: after ? { after, limit: 100 } : {} },
    })
    if (data) setMessages((current) => mergeMessages(current, data.items))
  }, [id, lastSentId, messages])

  useEffect(
    () =>
      realtime.subscribe((event) => {
        if (event.type === 'message.created' && event.message.conversation_id === id) {
          setMessages((current) => mergeMessages(current, [event.message]))
        } else if (event.type === 'conversation.read' && event.conversation_id === id) {
          setMembers((current) =>
            current.map((m) =>
              m.user.id === event.user_id &&
              (!m.last_read_message_id || m.last_read_message_id < event.message_id)
                ? { ...m, last_read_message_id: event.message_id }
                : m,
            ),
          )
        } else if (event.type === 'conversation.updated' && event.conversation_id === id) {
          router.refresh()
        } else if (event.type === 'reconnected') {
          void catchUp()
        }
      }),
    [catchUp, id, router],
  )

  // Read what's on screen, now and whenever the tab comes back.
  useEffect(() => {
    void markRead(messages)
    const onVisible = () => void markRead(messages)
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [markRead, messages])

  useLayoutEffect(() => {
    const el = list.current
    if (!el) return
    if (heightBeforeOlder.current !== null) {
      el.scrollTop += el.scrollHeight - heightBeforeOlder.current
      heightBeforeOlder.current = null
    } else if (pinned.current) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages])

  async function loadOlder() {
    if (!olderCursor || loadingOlder) return
    setLoadingOlder(true)
    const { data } = await browserApi.GET('/v1/conversations/{conversation_id}/messages', {
      params: { path: { conversation_id: id }, query: { before: olderCursor } },
    })
    setLoadingOlder(false)
    if (!data) return
    heightBeforeOlder.current = list.current?.scrollHeight ?? null
    setOlderCursor(data.older_cursor)
    setMessages((current) => mergeMessages(current, data.items))
  }

  async function deliver(message: ChatMessage) {
    const result = await attempt(() =>
      browserApi.POST('/v1/conversations/{conversation_id}/messages', {
        params: { path: { conversation_id: id } },
        body: { body: message.body, client_id: message.client_id },
      }),
    )
    if (result.ok) {
      setMessages((current) => mergeMessages(current, [result.data]))
    } else {
      setError(result.problem.message)
      setMessages((current) =>
        current.map((m) =>
          m.client_id === message.client_id && m.status ? { ...m, status: 'failed' } : m,
        ),
      )
    }
  }

  function send() {
    const text = body.trim()
    if (!text || text.length > MAX_MESSAGE_LENGTH) return
    const clientId = crypto.randomUUID()
    const pending: ChatMessage = {
      id: `pending-${clientId}`,
      client_id: clientId,
      conversation_id: id,
      sender: { ...me, username: me.username ?? '', headline: null },
      body: text,
      created_at: new Date().toISOString(),
      status: 'sending',
    }
    pinned.current = true
    setBody('')
    setError(null)
    setMessages((current) => mergeMessages(current, [pending]))
    void deliver(pending)
  }

  function retry(message: ChatMessage) {
    setError(null)
    setMessages((current) =>
      current.map((m) => (m.client_id === message.client_id ? { ...m, status: 'sending' } : m)),
    )
    void deliver(message)
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      send()
    }
  }

  const lastMine = messages.findLast((m) => m.sender?.id === me.id && !m.status)
  const seen = lastMine ? seenBy(members, lastMine.id, me.id) : []
  const isGroup = conversation.kind === 'group'

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ol
        ref={list}
        aria-label="Messages"
        aria-live="polite"
        onScroll={(e) => {
          const el = e.currentTarget
          pinned.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80
        }}
        className="min-h-0 flex-1 overflow-y-auto px-4 py-4"
      >
        {olderCursor ? (
          <li className="mb-4 flex justify-center">
            <Button size="sm" variant="ghost" disabled={loadingOlder} onClick={loadOlder}>
              {loadingOlder ? 'Loading…' : 'Older messages'}
            </Button>
          </li>
        ) : (
          <li className="mb-6 text-center font-mono text-xs text-ink-3">
            start of the conversation
          </li>
        )}
        {messages.map((m, index) => {
          const previous = messages[index - 1]
          const mine = m.sender?.id === me.id
          const startsGroup =
            !previous ||
            previous.sender?.id !== m.sender?.id ||
            Date.parse(m.created_at) - Date.parse(previous.created_at) > GROUP_GAP_MS
          return (
            <li
              key={m.client_id + (m.sender?.id ?? '')}
              className={cn(
                'flex gap-2.5',
                startsGroup ? 'mt-4' : 'mt-1',
                mine && 'flex-row-reverse',
              )}
            >
              <div className="w-8 shrink-0">
                {startsGroup && m.sender ? (
                  <Link href={`/u/${m.sender.username}` as Route}>
                    <Avatar
                      name={m.sender.display_name}
                      src={m.sender.avatar_url}
                      accent={m.sender.accent_color as Accent}
                      size="sm"
                    />
                  </Link>
                ) : null}
              </div>
              <div className={cn('grid max-w-[80%] gap-1', mine && 'justify-items-end')}>
                {startsGroup ? (
                  <div className="flex gap-2 font-mono text-xs text-ink-3">
                    {!mine ? (
                      <span className="text-ink-2">{m.sender?.display_name ?? 'Someone'}</span>
                    ) : null}
                    <time dateTime={m.created_at} title={new Date(m.created_at).toLocaleString()}>
                      {clock.format(new Date(m.created_at))}
                    </time>
                  </div>
                ) : null}
                <p
                  className={cn(
                    'border-2 px-3 py-2 break-words whitespace-pre-wrap',
                    mine
                      ? 'border-magenta bg-magenta-soft text-ink'
                      : 'border-line-strong bg-surface text-ink',
                    m.status === 'sending' && 'opacity-60',
                    m.status === 'failed' && 'border-coral',
                  )}
                >
                  {m.body}
                </p>
                {m.status === 'failed' ? (
                  <button
                    type="button"
                    onClick={() => retry(m)}
                    className="font-mono text-xs text-coral hover:underline"
                  >
                    not sent · retry
                  </button>
                ) : null}
                {m === lastMine && seen.length > 0 ? (
                  <span className="font-mono text-xs text-ink-3">
                    {isGroup
                      ? `seen by ${seen.map((s) => s.user.display_name).join(', ')}`
                      : 'seen'}
                  </span>
                ) : null}
              </div>
            </li>
          )
        })}
      </ol>
      {error ? (
        <Alert tone="error" className="mx-4 mb-2">
          {error}
        </Alert>
      ) : null}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
        className="flex items-end gap-2 border-t-2 border-line-strong bg-surface p-3"
      >
        <label htmlFor="message-body" className="sr-only">
          Message
        </label>
        <textarea
          id="message-body"
          rows={1}
          value={body}
          maxLength={MAX_MESSAGE_LENGTH}
          onChange={(e) => setBody(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Write a message"
          title="Enter sends. Shift+Enter starts a new line."
          className="max-h-40 min-h-10 flex-1 resize-y border-2 border-line-strong bg-sunk px-3 py-2 placeholder:text-ink-3 focus:border-magenta focus:outline-none"
        />
        <Button type="submit" disabled={!body.trim()} className="h-10 bg-magenta text-[#0c1017]">
          Send
        </Button>
      </form>
    </div>
  )
}
