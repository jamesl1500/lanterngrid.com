import { Button, Card } from '@lanterngrid/ui'
import Link from 'next/link'

export default function ProfileNotFound() {
  return (
    <main className="mx-auto grid max-w-md px-4 py-16">
      <Card raised className="grid gap-4 p-8">
        <span className="label">404</span>
        <h1 className="text-3xl font-bold">No one here by that name</h1>
        <p className="text-ink-2">
          Check the spelling, or the account may have changed its username.
        </p>
        <Button asChild variant="secondary" className="justify-self-start">
          <Link href="/">Go home</Link>
        </Button>
      </Card>
    </main>
  )
}
