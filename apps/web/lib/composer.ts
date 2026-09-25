/** The @name or #tag being typed right before the caret, if any. */
export function activeToken(text: string, caret: number) {
  const match = /(^|[\s(])([@#])([A-Za-z0-9_+#.-]{0,32})$/.exec(text.slice(0, caret))
  if (!match) return null
  const [, lead = '', trigger, query = ''] = match
  return {
    trigger: trigger as '@' | '#',
    query,
    start: match.index + lead.length,
    end: caret,
  }
}

/** Replace the token with `insert` and a space; returns the new text and caret position. */
export function insertAt(
  text: string,
  token: { start: number; end: number },
  insert: string,
): { text: string; caret: number } {
  const after = text.slice(token.end).replace(/^\S*/, '') // drop the rest of a half-typed word
  const next = `${text.slice(0, token.start)}${insert} ${after.replace(/^ /, '')}`
  return { text: next, caret: token.start + insert.length + 1 }
}

/** How a tag is inserted: its name when that has no spaces, otherwise its slug. */
export function tagText(tag: { name: string; slug: string }) {
  return /\s/.test(tag.name) ? `#${tag.slug}` : `#${tag.name}`
}
