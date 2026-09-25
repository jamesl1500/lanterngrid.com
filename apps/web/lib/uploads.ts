import type { Schemas } from '@lanterngrid/api-client'

import { browserApi } from './api'
import { attempt } from './errors'

export type UploadKind = Schemas['UploadRequest']['kind']
export type ImageKind = Exclude<UploadKind, 'post'>
type ImageType = Schemas['UploadRequest']['content_type']

const MB = 1024 * 1024
export const imageTypes: ImageType[] = ['image/png', 'image/jpeg', 'image/webp', 'image/gif']
export const maxImageBytes: Record<UploadKind, number> = {
  avatar: 2 * MB,
  banner: 5 * MB,
  post: 5 * MB,
}
const labels: Record<UploadKind, string> = { avatar: 'Avatars', banner: 'Banners', post: 'Images' }

/** Mirrors the API's checks so people hear about a wrong file before it uploads. */
export function imageProblem(kind: UploadKind, file: { type: string; size: number }) {
  if (!imageTypes.includes(file.type as ImageType)) return 'Use a PNG, JPEG, WebP or GIF image.'
  if (file.size > maxImageBytes[kind]) {
    return `${labels[kind]} can be up to ${maxImageBytes[kind] / MB} MB.`
  }
  return null
}

type Failure = { ok: false; message: string }

/** Ask the API for an upload URL and send the file straight to storage. Returns its key. */
export async function uploadFile(
  kind: UploadKind,
  file: File,
): Promise<{ ok: true; key: string } | Failure> {
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
  return { ok: true, key: ticket.data.key }
}

type Result = { ok: true; images: Schemas['ProfileImages'] } | Failure

/** Upload a profile image and attach it. */
export async function uploadImage(kind: ImageKind, file: File): Promise<Result> {
  const uploaded = await uploadFile(kind, file)
  if (!uploaded.ok) return uploaded

  const attached = await attempt(() =>
    browserApi.PUT('/v1/me/images/{kind}', {
      params: { path: { kind } },
      body: { key: uploaded.key },
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
