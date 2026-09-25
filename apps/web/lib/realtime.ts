import type { Message } from './messages'

import { browserApi } from './api'

export type RealtimeEvent =
  | { type: 'ready' }
  /** The socket came back after dropping: fetch whatever arrived in between. */
  | { type: 'reconnected' }
  | { type: 'message.created'; message: Message }
  | { type: 'conversation.read'; conversation_id: string; user_id: string; message_id: string }
  | { type: 'conversation.updated'; conversation_id: string }

type Handler = (event: RealtimeEvent) => void

/** 1s, 2s, 4s ... up to 30s, with some jitter so a restart doesn't reconnect everyone at once. */
export function retryDelay(attempt: number, random = Math.random) {
  const base = Math.min(30_000, 1000 * 2 ** attempt)
  return Math.round(base * (0.8 + random() * 0.4))
}

const PING_MS = 25_000

/**
 * One socket per tab, shared by every component that subscribes. It opens with the first
 * subscriber, reconnects when it drops and closes when nobody is listening.
 */
class Realtime {
  private handlers = new Set<Handler>()
  private socket: WebSocket | null = null
  private attempt = 0
  private connectedBefore = false
  private retryTimer: ReturnType<typeof setTimeout> | undefined
  private pingTimer: ReturnType<typeof setInterval> | undefined
  private closeTimer: ReturnType<typeof setTimeout> | undefined

  subscribe(handler: Handler) {
    this.handlers.add(handler)
    clearTimeout(this.closeTimer)
    if (!this.socket && this.retryTimer === undefined) void this.connect()
    return () => {
      this.handlers.delete(handler)
      // Navigating between pages swaps subscribers; don't drop the socket in between.
      if (this.handlers.size === 0) this.closeTimer = setTimeout(() => this.close(), 5000)
    }
  }

  private emit(event: RealtimeEvent) {
    for (const handler of this.handlers) handler(event)
  }

  private async connect() {
    this.retryTimer = undefined
    const { data } = await browserApi.POST('/v1/realtime/ticket').catch(() => ({ data: null }))
    if (!data) return this.retry()
    // Everyone unsubscribed while the ticket was on its way.
    if (this.handlers.size === 0) return
    const socket = new WebSocket(`${data.url}?ticket=${encodeURIComponent(data.ticket)}`)
    this.socket = socket
    socket.onmessage = (message) => {
      let event: RealtimeEvent
      try {
        event = JSON.parse(String(message.data)) as RealtimeEvent
      } catch {
        return
      }
      if (event.type === 'ready') {
        this.attempt = 0
        if (this.connectedBefore) this.emit({ type: 'reconnected' })
        this.connectedBefore = true
      }
      this.emit(event)
    }
    socket.onopen = () => {
      clearInterval(this.pingTimer)
      this.pingTimer = setInterval(() => socket.send('{"type":"ping"}'), PING_MS)
    }
    socket.onclose = () => {
      clearInterval(this.pingTimer)
      if (this.socket === socket) this.socket = null
      if (this.handlers.size > 0) this.retry()
    }
  }

  private retry() {
    if (this.handlers.size === 0 || this.retryTimer !== undefined) return
    this.retryTimer = setTimeout(() => void this.connect(), retryDelay(this.attempt++))
  }

  private close() {
    clearInterval(this.pingTimer)
    clearTimeout(this.retryTimer)
    this.retryTimer = undefined
    this.socket?.close()
    this.socket = null
    this.connectedBefore = false
  }
}

export const realtime = new Realtime()
