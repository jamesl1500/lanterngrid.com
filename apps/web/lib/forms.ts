import type { FieldValues, Path, UseFormSetError } from 'react-hook-form'

/** Put the API's per-field messages onto the matching form fields. */
export function applyFieldErrors<T extends FieldValues>(
  setError: UseFormSetError<T>,
  fields: Record<string, string>,
) {
  for (const [name, message] of Object.entries(fields)) {
    setError(name as Path<T>, { message })
  }
}
