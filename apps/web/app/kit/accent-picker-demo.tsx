'use client'

import { AccentPicker, type Accent } from '@lanterngrid/ui'
import { useState } from 'react'

export function AccentPickerDemo() {
  const [accent, setAccent] = useState<Accent>('violet')
  return <AccentPicker name="kit-accent" value={accent} onChange={setAccent} />
}
