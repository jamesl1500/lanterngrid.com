/** Wide screens: nothing open yet. Phones only see the inbox. */
export default function MessagesPage() {
  return (
    <section className="hidden place-items-center bg-grid px-6 text-center lg:grid">
      <div className="grid gap-2">
        <span className="label">no conversation open</span>
        <p className="max-w-[36ch] text-ink-2">Pick one on the left, or start a new one.</p>
      </div>
    </section>
  )
}
