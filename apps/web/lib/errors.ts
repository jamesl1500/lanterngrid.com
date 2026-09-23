type ValidationItem = { loc: (string | number)[]; msg: string }

export type ApiProblem = {
  /** One sentence to show above the form. */
  message: string
  /** Messages for specific fields, keyed by field name. */
  fields: Record<string, string>
}

const FALLBACK = 'Something went wrong. Try again in a moment.'

/** Turn a FastAPI error body (or a network failure) into something a form can show. */
export function toProblem(error: unknown): ApiProblem {
  const detail = (error as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return { message: detail, fields: {} }
  if (Array.isArray(detail)) {
    const fields: Record<string, string> = {}
    for (const item of detail as ValidationItem[]) {
      const field = item.loc.at(-1)
      if (typeof field === 'string' && !(field in fields)) {
        fields[field] = item.msg.replace(/^Value error, /, '')
      }
    }
    return { message: 'Check the highlighted fields.', fields }
  }
  return { message: FALLBACK, fields: {} }
}

type ApiCall<T> = Promise<{ data?: T; error?: unknown; response: Response }>

/** Run an API call from a form and return either its data or a problem to show. */
export async function attempt<T>(
  call: () => ApiCall<T>,
): Promise<{ ok: true; data: T } | { ok: false; problem: ApiProblem }> {
  try {
    const { data, error, response } = await call()
    if (response.ok) return { ok: true, data: data as T }
    return { ok: false, problem: toProblem(error) }
  } catch {
    return { ok: false, problem: toProblem(undefined) }
  }
}
