'use client'

import { Field, TagInput, type TagSuggestion } from '@lanterngrid/ui'
import { useState } from 'react'

const sample = ['TypeScript', 'Terraform', 'Tailwind CSS', 'Rust', 'Redis', 'React', 'Postgres']

// Local suggestions so the kit works without the API.
async function suggest(q: string): Promise<TagSuggestion[]> {
  return sample
    .filter((name) => name.toLowerCase().startsWith(q.trim().toLowerCase()))
    .map((name) => ({ slug: name.toLowerCase(), name }))
}

export function TagInputDemo() {
  const [tags, setTags] = useState(['Rust', 'Postgres'])
  return (
    <Field id="kit-stack" label="Stack" hint="Type, then Enter or comma. Try “t”.">
      <TagInput
        id="kit-stack"
        value={tags}
        onChange={setTags}
        suggest={suggest}
        aria-describedby="kit-stack-hint"
      />
    </Field>
  )
}
