import {
  accents,
  accentClasses,
  Avatar,
  Button,
  Card,
  CardBody,
  CardHeader,
  contentKinds,
  KindBadge,
  Tag,
} from '@lanterngrid/ui'
import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { SamplePost } from '@/components/sample-post'

export const metadata: Metadata = { title: 'UI kit' }

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="grid gap-4">
      <h2 className="border-b-2 border-line-strong pb-2 text-xl font-bold">{title}</h2>
      {children}
    </section>
  )
}

export default function KitPage() {
  return (
    <main className="mx-auto grid max-w-5xl gap-12 px-4 py-10">
      <header className="grid gap-2">
        <span className="label">design system</span>
        <h1 className="text-4xl font-bold">UI kit</h1>
        <p className="max-w-[60ch] text-ink-2">
          Every shared component from <code className="font-mono">@lanterngrid/ui</code>. Sharp
          corners, hard borders, hard shadows, one accent per content kind.
        </p>
      </header>

      <Section title="Color">
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
          {accents.map((a) => (
            <div key={a} className="border border-line-strong bg-surface">
              <div className={`h-12 ${accentClasses[a].solid}`} />
              <div className="border-t border-line-strong px-2 py-1 font-mono text-xs text-ink-2">
                {a}
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Type">
        <div className="grid gap-2">
          <span className="font-display text-3xl font-bold">Chakra Petch for display</span>
          <span className="text-lg">IBM Plex Sans for reading, calm and technical.</span>
          <span className="font-mono text-ink-2">
            JetBrains Mono for code, handles and metadata
          </span>
        </div>
      </Section>

      <Section title="Buttons">
        <div className="flex flex-wrap items-center gap-3">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="accent">Accent</Button>
          <Button variant="ghost">Ghost</Button>
          <Button size="sm">Small</Button>
          <Button size="lg">Large</Button>
          <Button disabled>Disabled</Button>
        </div>
      </Section>

      <Section title="Badges, tags and avatars">
        <div className="flex flex-wrap items-center gap-2">
          {contentKinds.map((k) => (
            <KindBadge key={k} kind={k} />
          ))}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {accents.map((a) => (
            <Tag key={a} name={a} accent={a} />
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {accents.map((a, i) => (
            <Avatar
              key={a}
              name={
                ['Ada Park', 'Linus T', 'Grace Hopper', 'Ken Thompson', 'Margaret H', 'Dennis R'][
                  i
                ] ?? a
              }
              accent={a}
              size={i === 0 ? 'lg' : 'md'}
            />
          ))}
        </div>
      </Section>

      <Section title="Cards">
        <div className="grid items-start gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <span className="label">flat card</span>
            </CardHeader>
            <CardBody>
              <p className="text-ink-2">
                Hairline border for structure. Most surfaces look like this.
              </p>
            </CardBody>
          </Card>
          <SamplePost />
        </div>
      </Section>
    </main>
  )
}
