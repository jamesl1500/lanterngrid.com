'use client'

import { HighlightStyle, LanguageDescription, syntaxHighlighting } from '@codemirror/language'
import { languages } from '@codemirror/language-data'
import { Compartment } from '@codemirror/state'
import { EditorView, keymap } from '@codemirror/view'
import { tags as t } from '@lezer/highlight'
import { basicSetup } from 'codemirror'
import { useEffect, useRef } from 'react'

import { languageLabels, type Language } from '@/lib/snippets'

// The same token colors as rendered code (see --shiki-* in globals.css).
const highlightStyle = HighlightStyle.define([
  {
    tag: [t.keyword, t.operatorKeyword, t.modifier, t.controlKeyword],
    color: 'var(--shiki-token-keyword)',
  },
  { tag: [t.string, t.special(t.string), t.regexp], color: 'var(--shiki-token-string)' },
  {
    tag: [t.number, t.bool, t.null, t.atom, t.constant(t.name)],
    color: 'var(--shiki-token-constant)',
  },
  { tag: [t.comment, t.meta], color: 'var(--shiki-token-comment)', fontStyle: 'italic' },
  {
    tag: [
      t.function(t.variableName),
      t.function(t.propertyName),
      t.definition(t.function(t.variableName)),
    ],
    color: 'var(--shiki-token-function)',
  },
  { tag: [t.typeName, t.className, t.tagName], color: 'var(--shiki-token-parameter)' },
  { tag: [t.punctuation, t.bracket, t.operator], color: 'var(--shiki-token-punctuation)' },
  { tag: t.link, color: 'var(--shiki-token-link)', textDecoration: 'underline' },
])

const theme = EditorView.theme({
  '&': { color: 'var(--lg-ink)', backgroundColor: 'var(--lg-sunk)', fontSize: '13px' },
  '&.cm-focused': { outline: 'none' },
  '.cm-scroller': {
    fontFamily: "var(--font-jetbrains), 'JetBrains Mono', ui-monospace, monospace",
    lineHeight: '1.6',
    minHeight: '16rem',
    maxHeight: '36rem',
  },
  '.cm-content': { caretColor: 'var(--lg-ink)', padding: '0.75rem 0' },
  '.cm-cursor': { borderLeftColor: 'var(--lg-ink)' },
  '.cm-gutters': {
    backgroundColor: 'var(--lg-sunk)',
    color: 'var(--lg-ink-3)',
    border: 'none',
    borderRight: '1px solid var(--lg-line)',
  },
  '.cm-activeLine, .cm-activeLineGutter': { backgroundColor: 'transparent' },
  '&.cm-focused .cm-activeLine': {
    backgroundColor: 'color-mix(in srgb, var(--lg-violet) 8%, transparent)',
  },
  '.cm-selectionBackground, &.cm-focused .cm-selectionBackground, ::selection': {
    backgroundColor: 'color-mix(in srgb, var(--lg-violet) 30%, transparent) !important',
  },
  '.cm-tooltip': {
    border: '2px solid var(--lg-line-strong)',
    backgroundColor: 'var(--lg-surface)',
  },
})

type Props = {
  /** Only read when the editor starts; after that the editor owns the text. */
  initialValue: string
  onChange: (value: string) => void
  language: Language
  labelledBy: string
  /** Called on Ctrl/Cmd+Enter. */
  onSubmit?: () => void
}

/** A code editor that highlights the chosen language. Languages load on demand. */
export function CodeEditor({ initialValue, onChange, language, labelledBy, onSubmit }: Props) {
  const host = useRef<HTMLDivElement>(null)
  const view = useRef<EditorView | null>(null)
  const languageSlot = useRef(new Compartment())
  const initial = useRef(initialValue)
  const handlers = useRef({ onChange, onSubmit })

  useEffect(() => {
    handlers.current = { onChange, onSubmit }
  })

  useEffect(() => {
    if (!host.current) return
    const editor = new EditorView({
      parent: host.current,
      doc: initial.current,
      extensions: [
        keymap.of([
          {
            key: 'Mod-Enter',
            run: () => {
              handlers.current.onSubmit?.()
              return true
            },
          },
        ]),
        basicSetup,
        theme,
        syntaxHighlighting(highlightStyle),
        languageSlot.current.of([]),
        EditorView.contentAttributes.of({ 'aria-labelledby': labelledBy }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) handlers.current.onChange(update.state.doc.toString())
        }),
      ],
    })
    view.current = editor
    return () => {
      editor.destroy()
      view.current = null
    }
  }, [labelledBy])

  useEffect(() => {
    const slot = languageSlot.current
    const description =
      language === 'text'
        ? null
        : LanguageDescription.matchLanguageName(languages, languageLabels[language], true)
    if (!description) {
      view.current?.dispatch({ effects: slot.reconfigure([]) })
      return
    }
    let cancelled = false
    void description.load().then((support) => {
      if (!cancelled) view.current?.dispatch({ effects: slot.reconfigure(support) })
    })
    return () => {
      cancelled = true
    }
  }, [language])

  return <div ref={host} className="border-2 border-line-strong" />
}
