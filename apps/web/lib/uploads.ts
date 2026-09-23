import type { Schemas } from '@lanterngrid/api-client'

import { browserApi } from './api'
import { attempt } from './errors'

export type ImageKind = Schemas['UploadRequest']['kind']
type ImageType = Schemas['UploadRequest']['content_type']

const MB = 1024 * 1024
export const imageTypes: ImageType[] = ['image/png', 'image/jpeg', 'image/webp', 'image/gif']
export const maxImageBytes: Record<ImageKind, number> = { avatar: 2 * MB, banner: 5 * MB }

/** Mirrors the API's checks so people hear about a wrong file before it uploads. */
export function imageProblem(kind: ImageKind, file: { type: string; size: number }) {
  if (!imageTypes.includes(file.type as ImageType)) return 'Use a PNG, JPEG, WebP or GIF image.'
  if (file.size > maxImageBytes[kind]) {
    const label = kind === 'avatar' ? 'Avatars' : 'Banners'
    return `${label} can be up to ${maxImageBytes[kind] / MB} MB.`
  }
  return null
}

type Result = { ok: true; images: Schemas['ProfileImages'] } | { ok: false; message: string }

/** Ask the API for an upload URL, send the file straight to storage, then attach it. */
export async function uploadImage(kind: ImageKind, file: File): Promise<Result> {
  const problem = imageProblem(kind, file)
  if (problem) return { ok: false, message: problem }

  const ticket = await attempt(() =>
    browserApi.POST('/v1/me/uploads', {
      body: { kind, content_type: file.type as ImageType, size: file.size },
    }),
  )
  if (!ticket.ok) return { ok: false, message: ticket.problem.message }

  try {
    const put = await fetch(ticket.data.upload_url, {
      method: 'PUT',
      headers: ticket.data.headers,
      body: file,
    })
    if (!put.ok) throw new Error(String(put.status))
  } catch {
    return { ok: false, message: "The upload didn't go through. Try again." }
  }

  const attached = await attempt(() =>
    browserApi.PUT('/v1/me/images/{kind}', {
      params: { path: { kind } },
      body: { key: ticket.data.key },
    }),
  )
  if (!attached.ok) return { ok: false, message: attached.problem.message }
  return { ok: true, images: attached.data }
}

export async function removeImage(kind: ImageKind): Promise<Result> {
  const result = await attempt(() =>
    browserApi.DELETE('/v1/me/images/{kind}', { params: { path: { kind } } }),
  )
  return result.ok
    ? { ok: true, images: result.data }
    : { ok: false, message: result.problem.message }
}
