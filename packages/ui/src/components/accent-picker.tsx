'use client'

import { cn } from '../lib/cn'
import { accentClasses, accents, type Accent } from '../lib/kinds'

export type AccentPickerProps = {
  name: string
  value: Accent
  onChange: (accent: Accent) => void
  label?: string
}

/** Pick one of the six accent colors. A radio group, so arrow keys move between swatches. */
export function AccentPicker({ name, value, onChange, label = 'Accent color' }: AccentPickerProps) {
  return (
    <fieldset className="grid gap-1.5">
      <legend className="mb-1.5 font-mono text-xs tracking-[0.08em] text-ink-2 uppercase">
        {label}
      </legend>
      <div className="flex flex-wrap gap-2">
        {accents.map((accent) => (
          <label key={accent} className="cursor-pointer">
            <input
              type="radio"
              name={name}
              value={accent}
              checked={value === accent}
              onChange={() => onChange(accent)}
              className="peer sr-only"
            />
            <span
              className={cn(
                'block size-9 border-2 border-line-strong transition-transform',
                'peer-checked:-translate-x-px peer-checked:-translate-y-px peer-checked:shadow-hard',
                'peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-magenta',
                accentClasses[accent].solid,
              )}
            />
            <span className="sr-only">{accent}</span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
