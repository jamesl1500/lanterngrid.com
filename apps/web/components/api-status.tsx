import { Card, CardHeader, cn } from '@lanterngrid/ui'

import { serverApi } from '@/lib/api'
import { describeHealth, type Health, type StatusTone } from '@/lib/health'

const toneClass: Record<StatusTone, string> = {
  ok: 'bg-lime',
  warn: 'bg-amber',
  down: 'bg-coral',
}

async function fetchHealth(): Promise<Health | null> {
  try {
    const { data } = await serverApi().GET('/v1/health', { cache: 'no-store' })
    return data ?? null
  } catch {
    return null
  }
}

/** Live status of the backend services, so a broken local setup is obvious at a glance. */
export async function ApiStatus() {
  const rows = describeHealth(await fetchHealth())
  return (
    <Card>
      <CardHeader>
        <span className="label">system status</span>
      </CardHeader>
      <ul className="divide-y divide-line font-mono text-sm">
        {rows.map((row) => (
          <li key={row.name} className="flex items-center gap-3 px-4 py-2">
            <span aria-hidden className={cn('size-2.5', toneClass[row.tone])} />
            <span>{row.name}</span>
            <span className="ml-auto text-ink-3">{row.detail}</span>
          </li>
        ))}
      </ul>
    </Card>
  )
}
