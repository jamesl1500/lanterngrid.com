'use client'

import { Button, Dialog } from '@lanterngrid/ui'
import { useState } from 'react'

export function DialogDemo() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <Button variant="secondary" onClick={() => setOpen(true)}>
        Open a dialog
      </Button>
      <Dialog open={open} onClose={() => setOpen(false)} title="Report this post" accent="coral">
        <p className="text-ink-2">
          A modal on the native dialog element: Escape or a click outside closes it, and focus stays
          inside while it&apos;s open.
        </p>
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button size="sm" className="bg-coral text-[#0c1017]" onClick={() => setOpen(false)}>
            Send report
          </Button>
        </div>
      </Dialog>
    </>
  )
}
