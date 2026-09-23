import { describeHealth } from './health'

describe('describeHealth', () => {
  it('reports the API as down when the request failed', () => {
    expect(describeHealth(null)).toEqual([{ name: 'api', tone: 'down', detail: 'unreachable' }])
  })

  it('flags a degraded API and the service that is down', () => {
    const rows = describeHealth({
      status: 'degraded',
      version: '0.1.0',
      checks: { database: 'ok', redis: 'down' },
    })
    expect(rows).toEqual([
      { name: 'api', tone: 'warn', detail: 'v0.1.0' },
      { name: 'postgres', tone: 'ok', detail: 'ok' },
      { name: 'redis', tone: 'down', detail: 'down' },
    ])
  })
})
