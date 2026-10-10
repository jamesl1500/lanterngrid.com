'use server'

import { highlight } from '@/lib/highlight'

/** Most code highlighted per call: chat previews are a few lines. */
const MAX_PREVIEW = 4000

/** Highlighted HTML for a snippet preview in a chat, where messages arrive in the browser. */
export async function highlightPreview(code: string, lang: string) {
  return highlight(code.slice(0, MAX_PREVIEW), lang)
}
