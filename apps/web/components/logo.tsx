import Link from 'next/link'

export function Logo() {
  return (
    <Link href="/" className="font-display text-xl font-bold tracking-tight text-ink">
      Lantern Grid<span className="text-amber">_</span>
    </Link>
  )
}
