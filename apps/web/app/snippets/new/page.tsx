import type { Metadata } from 'next'

import { SnippetForm } from '@/components/snippet-form'
import { requireMe } from '@/lib/session'

export const metadata: Metadata = { title: 'New snippet' }

export default async function NewSnippetPage() {
  await requireMe('/snippets/new')
  return (
    <main className="mx-auto grid max-w-3xl grid-cols-1 gap-6 px-4 py-8">
      <header className="grid gap-1">
        <span className="label text-violet">snippet</span>
        <h1 className="text-3xl font-bold">New snippet</h1>
        <p className="text-ink-2">
          Save code worth keeping. Pin it to your profile or share it to your feed once it&apos;s
          saved.
        </p>
      </header>
      <SnippetForm />
    </main>
  )
}
