import { cn } from '@lanterngrid/ui'

/** A plain GET form to /search, so it works before any JavaScript loads. */
export function SearchBox({
  defaultValue = '',
  tab,
  autoFocus,
  className,
}: {
  defaultValue?: string
  tab?: string
  autoFocus?: boolean
  className?: string
}) {
  return (
    <form action="/search" role="search" className={cn('flex', className)}>
      <label htmlFor="search-q" className="sr-only">
        Search posts
      </label>
      <input
        id="search-q"
        name="q"
        type="search"
        defaultValue={defaultValue}
        autoFocus={autoFocus}
        maxLength={200}
        placeholder='Search posts: postgres, "borrow checker", rust -async'
        className="h-10 min-w-0 flex-1 border-2 border-r-0 border-line-strong bg-surface px-3 placeholder:text-ink-3 focus:shadow-hard-sm focus:outline-none"
      />
      {tab ? <input type="hidden" name="tab" value={tab} /> : null}
      <button
        type="submit"
        className="h-10 border-2 border-line-strong bg-cyan px-4 font-mono text-sm font-bold text-[#0c1017] hover:brightness-110"
      >
        Search
      </button>
    </form>
  )
}
