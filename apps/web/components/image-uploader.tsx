'use client'

import { accentClasses, Alert, Avatar, Button, cn, type Accent } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useRef, useState, type ChangeEvent } from 'react'

import { imageTypes, maxImageBytes, removeImage, uploadImage, type ImageKind } from '@/lib/uploads'

type Props = {
  kind: ImageKind
  url: string | null
  name: string
  accent: Accent
}

const copy: Record<ImageKind, { title: string; hint: string }> = {
  avatar: { title: 'Avatar', hint: 'Square works best.' },
  banner: { title: 'Banner', hint: 'Wide works best, around 1500 × 400.' },
}

/** Upload, replace or remove the avatar or banner. Files go straight to storage. */
export function ImageUploader({ kind, url: initialUrl, name, accent }: Props) {
  const router = useRouter()
  const input = useRef<HTMLInputElement>(null)
  const [url, setUrl] = useState(initialUrl)
  const [busy, setBusy] = useState<'uploading' | 'removing' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputId = `${kind}-file`

  async function run(action: 'uploading' | 'removing', work: () => ReturnType<typeof removeImage>) {
    setBusy(action)
    setError(null)
    const result = await work()
    setBusy(null)
    if (!result.ok) {
      setError(result.message)
      return
    }
    setUrl(kind === 'avatar' ? result.images.avatar_url : result.images.banner_url)
    router.refresh()
  }

  function onPick(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = '' // so picking the same file again still fires
    if (file) void run('uploading', () => uploadImage(kind, file))
  }

  const limitMb = maxImageBytes[kind] / (1024 * 1024)

  return (
    <div className="grid gap-3">
      <h3 id={`${kind}-title`} className="font-mono text-xs tracking-[0.08em] text-ink-2 uppercase">
        {copy[kind].title}
      </h3>
      <div className={cn('flex gap-4', kind === 'banner' ? 'flex-col' : 'items-center')}>
        {kind === 'avatar' ? (
          <Avatar name={name} src={url} accent={accent} size="lg" />
        ) : (
          <div
            role="img"
            aria-label={url ? 'Your banner' : 'No banner yet'}
            className={cn(
              'bg-grid h-24 border-2 border-line-strong bg-cover bg-center sm:h-28',
              !url && accentClasses[accent].soft,
            )}
            style={url ? { backgroundImage: `url(${JSON.stringify(url)})` } : undefined}
          />
        )}
        <div className="grid gap-2">
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={busy !== null}
              aria-describedby={`${kind}-hint`}
              onClick={() => input.current?.click()}
            >
              {busy === 'uploading' ? 'Uploading…' : url ? 'Replace' : 'Upload image'}
            </Button>
            {url ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                disabled={busy !== null}
                onClick={() => void run('removing', () => removeImage(kind))}
              >
                {busy === 'removing' ? 'Removing…' : 'Remove'}
              </Button>
            ) : null}
          </div>
          <p id={`${kind}-hint`} className="text-sm text-ink-3">
            PNG, JPEG, WebP or GIF, up to {limitMb} MB. {copy[kind].hint}
          </p>
        </div>
      </div>
      <input
        ref={input}
        id={inputId}
        type="file"
        accept={imageTypes.join(',')}
        className="sr-only"
        tabIndex={-1}
        aria-labelledby={`${kind}-title`}
        onChange={onPick}
      />
      {error ? <Alert tone="error">{error}</Alert> : null}
    </div>
  )
}
