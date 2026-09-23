import type { ReactNode } from 'react'

import { SettingsNav } from './settings-nav'

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <main className="mx-auto grid max-w-4xl gap-8 px-4 py-10 md:grid-cols-[180px_1fr]">
      <div className="grid content-start gap-4">
        <h1 className="text-2xl font-bold">Settings</h1>
        <SettingsNav />
      </div>
      <div className="min-w-0">{children}</div>
    </main>
  )
}
