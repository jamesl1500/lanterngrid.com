import type { Schemas } from '@lanterngrid/api-client'

export type Snippet = Schemas['SnippetOut']
export type SnippetPage = Schemas['SnippetPage']
export type Language = Schemas['SnippetCreate']['language']
export type Pins = Schemas['Pins']

export const MAX_SNIPPET_LENGTH = 50_000

/** Every language the API accepts, with the name people know it by. */
export const languageLabels: Record<Language, string> = {
  text: 'Plain text',
  bash: 'Bash',
  c: 'C',
  clojure: 'Clojure',
  cpp: 'C++',
  csharp: 'C#',
  css: 'CSS',
  dart: 'Dart',
  diff: 'Diff',
  dockerfile: 'Dockerfile',
  elixir: 'Elixir',
  erlang: 'Erlang',
  fsharp: 'F#',
  go: 'Go',
  graphql: 'GraphQL',
  haskell: 'Haskell',
  hcl: 'HCL',
  html: 'HTML',
  java: 'Java',
  javascript: 'JavaScript',
  json: 'JSON',
  jsx: 'JSX',
  julia: 'Julia',
  kotlin: 'Kotlin',
  lua: 'Lua',
  markdown: 'Markdown',
  nix: 'Nix',
  ocaml: 'OCaml',
  php: 'PHP',
  powershell: 'PowerShell',
  python: 'Python',
  r: 'R',
  ruby: 'Ruby',
  rust: 'Rust',
  scala: 'Scala',
  scss: 'SCSS',
  sql: 'SQL',
  svelte: 'Svelte',
  swift: 'Swift',
  toml: 'TOML',
  tsx: 'TSX',
  typescript: 'TypeScript',
  vue: 'Vue',
  xml: 'XML',
  yaml: 'YAML',
  zig: 'Zig',
}

/** Languages sorted by name, plain text first, for pickers. */
export const languageOptions = (Object.keys(languageLabels) as Language[]).sort((a, b) =>
  a === 'text' ? -1 : b === 'text' ? 1 : languageLabels[a].localeCompare(languageLabels[b]),
)

const byExtension: Record<string, Language> = {
  sh: 'bash',
  bash: 'bash',
  zsh: 'bash',
  c: 'c',
  h: 'c',
  clj: 'clojure',
  cc: 'cpp',
  cpp: 'cpp',
  cxx: 'cpp',
  hpp: 'cpp',
  cs: 'csharp',
  css: 'css',
  dart: 'dart',
  diff: 'diff',
  patch: 'diff',
  ex: 'elixir',
  exs: 'elixir',
  erl: 'erlang',
  fs: 'fsharp',
  go: 'go',
  graphql: 'graphql',
  gql: 'graphql',
  hs: 'haskell',
  tf: 'hcl',
  hcl: 'hcl',
  html: 'html',
  java: 'java',
  js: 'javascript',
  mjs: 'javascript',
  cjs: 'javascript',
  json: 'json',
  jsx: 'jsx',
  jl: 'julia',
  kt: 'kotlin',
  kts: 'kotlin',
  lua: 'lua',
  md: 'markdown',
  nix: 'nix',
  ml: 'ocaml',
  php: 'php',
  ps1: 'powershell',
  py: 'python',
  r: 'r',
  rb: 'ruby',
  rs: 'rust',
  scala: 'scala',
  scss: 'scss',
  sql: 'sql',
  svelte: 'svelte',
  swift: 'swift',
  toml: 'toml',
  tsx: 'tsx',
  ts: 'typescript',
  mts: 'typescript',
  vue: 'vue',
  xml: 'xml',
  yml: 'yaml',
  yaml: 'yaml',
  zig: 'zig',
}

/** Guess the language from a filename like `main.rs` or `Dockerfile`. */
export function languageFromFilename(filename: string): Language | null {
  const name = filename.trim().toLowerCase()
  if (name === 'dockerfile' || name.endsWith('.dockerfile')) return 'dockerfile'
  const dot = name.lastIndexOf('.')
  if (dot < 0) return null
  return byExtension[name.slice(dot + 1)] ?? null
}
