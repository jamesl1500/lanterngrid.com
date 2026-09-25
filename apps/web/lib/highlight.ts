import 'server-only'

import {
  bundledLanguages,
  createCssVariablesTheme,
  createHighlighter,
  type BundledLanguage,
  type Highlighter,
} from 'shiki'

// Colors come from CSS variables (see globals.css), so code follows the site's accents and
// switches with the light and dark themes.
const theme = createCssVariablesTheme({ name: 'lantern', variablePrefix: '--shiki-' })

let highlighter: Promise<Highlighter> | undefined

function getHighlighter() {
  highlighter ??= createHighlighter({ themes: [theme], langs: [] })
  return highlighter
}

export function isLanguage(lang: string | undefined): lang is BundledLanguage {
  return !!lang && Object.hasOwn(bundledLanguages, lang)
}

/** Highlighted HTML for a code block. Unknown languages come back as escaped plain text. */
export async function highlight(code: string, lang: string | undefined) {
  const h = await getHighlighter()
  const language = isLanguage(lang) ? lang : 'text'
  if (language !== 'text' && !h.getLoadedLanguages().includes(language)) {
    await h.loadLanguage(language)
  }
  return h.codeToHtml(code, { lang: language, theme: 'lantern' })
}
