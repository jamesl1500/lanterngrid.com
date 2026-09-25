import Link from 'next/link'

export function Logo() {
  return (
    <Link
      href="/"
      className="shrink-0 font-display text-xl font-bold tracking-tight whitespace-nowrap text-ink"
    >
      Lantern Grid<span className="text-amber">_</span>
    </Link>
  )
}
