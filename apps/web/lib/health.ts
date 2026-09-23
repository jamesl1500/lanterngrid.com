import type { Schemas } from '@lanterngrid/api-client'

export type Health = Schemas['HealthResponse']
export type StatusTone = 'ok' | 'warn' | 'down'

export type ServiceRow = { name: string; tone: StatusTone; detail: string }

/** Turn the API's health payload (or a failed request) into rows for the status panel. */
export function describeHealth(health: Health | null): ServiceRow[] {
  if (!health) {
    return [{ name: 'api', tone: 'down', detail: 'unreachable' }]
  }
  return [
    { name: 'api', tone: health.status === 'ok' ? 'ok' : 'warn', detail: `v${health.version}` },
    {
      name: 'postgres',
      tone: health.checks.database === 'ok' ? 'ok' : 'down',
      detail: health.checks.database,
    },
    {
      name: 'redis',
      tone: health.checks.redis === 'ok' ? 'ok' : 'down',
      detail: health.checks.redis,
    },
  ]
}
