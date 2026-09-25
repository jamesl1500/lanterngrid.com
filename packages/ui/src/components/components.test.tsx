import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'

import { AccentPicker } from './accent-picker'
import { Avatar, initials } from './avatar'
import { Button } from './button'
import { describedBy, Field, SelectField } from './field'
import { Input } from './input'
import { KindBadge } from './kind-badge'
import { Tag } from './tag'
import { TagInput } from './tag-input'

describe('Button', () => {
  it('renders a button with the primary style by default', () => {
    render(<Button>Post</Button>)
    const button = screen.getByRole('button', { name: 'Post' })
    expect(button).toHaveClass('bg-ink')
  })

  it('renders its child element when asChild is set', () => {
    render(
      <Button asChild variant="secondary">
        <a href="/feed">Open feed</a>
      </Button>,
    )
    const link = screen.getByRole('link', { name: 'Open feed' })
    expect(link).toHaveAttribute('href', '/feed')
    expect(link).toHaveClass('bg-surface')
  })
})

describe('Avatar', () => {
  it('builds initials from the first and last name', () => {
    expect(initials('Ada Lovelace Park')).toBe('AP')
    expect(initials('linus')).toBe('L')
    expect(initials('  ')).toBe('?')
  })

  it('shows initials when there is no image', () => {
    render(<Avatar name="Grace Hopper" />)
    expect(screen.getByRole('img', { name: 'Grace Hopper' })).toHaveTextContent('GH')
  })
})

describe('Tag and KindBadge', () => {
  it('prefixes tags with #', () => {
    render(<Tag name="postgres" />)
    expect(screen.getByText('#postgres')).toBeInTheDocument()
  })

  it('colors a badge by its content kind', () => {
    render(<KindBadge kind="snippet" />)
    expect(screen.getByText('snippet')).toHaveClass('text-violet')
  })
})

describe('Field and Input', () => {
  it('labels the control and shows the error instead of the hint', () => {
    render(
      <Field id="email" label="Email" hint="We never share it" error="Enter an email">
        <Input id="email" aria-invalid aria-describedby={describedBy('email', { error: 'x' })} />
      </Field>,
    )
    const input = screen.getByLabelText('Email')
    expect(input).toHaveAttribute('aria-describedby', 'email-error')
    expect(screen.getByText('Enter an email')).toBeInTheDocument()
    expect(screen.queryByText('We never share it')).not.toBeInTheDocument()
  })
})

describe('AccentPicker', () => {
  it('reports the chosen accent', async () => {
    const onChange = vi.fn()
    render(<AccentPicker name="accent" value="violet" onChange={onChange} />)
    screen.getByLabelText('lime').click()
    expect(onChange).toHaveBeenCalledWith('lime')
    expect(screen.getByLabelText('violet')).toBeChecked()
  })
})

describe('Select', () => {
  it('wires the label and error to the native select', () => {
    render(
      <SelectField id="kind" label="Kind" error="Pick one.">
        <option value="github">GitHub</option>
      </SelectField>,
    )
    const select = screen.getByRole('combobox', { name: 'Kind' })
    expect(select).toHaveAttribute('aria-invalid', 'true')
    expect(select).toHaveAccessibleDescription('Pick one.')
  })
})

describe('TagInput', () => {
  function Harness({
    initial = [],
    max,
    suggest,
  }: {
    initial?: string[]
    max?: number
    suggest?: (q: string) => Promise<{ slug: string; name: string }[]>
  }) {
    const [tags, setTags] = useState(initial)
    return (
      <>
        <label htmlFor="stack">Stack</label>
        <TagInput id="stack" value={tags} onChange={setTags} max={max} suggest={suggest} />
        <output>{tags.join('|')}</output>
      </>
    )
  }

  it('adds tags on Enter and comma, skips duplicates and removes with Backspace', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    const input = screen.getByRole('combobox', { name: 'Stack' })
    await user.type(input, 'Rust{Enter}Postgres,rust{Enter}')
    expect(screen.getByRole('status')).toHaveTextContent('Rust|Postgres')
    await user.type(input, '{Backspace}')
    expect(screen.getByRole('status')).toHaveTextContent(/^Rust$/)
    await user.click(screen.getByRole('button', { name: 'Remove Rust' }))
    expect(screen.getByRole('status')).toBeEmptyDOMElement()
  })

  it('stops at the maximum', async () => {
    render(<Harness initial={['Go', 'Zig']} max={2} />)
    expect(screen.getByRole('combobox', { name: 'Stack' })).toBeDisabled()
  })

  it('picks a suggestion with the arrow keys', async () => {
    const user = userEvent.setup()
    const suggest = async (q: string) =>
      [
        { slug: 'typescript', name: 'TypeScript' },
        { slug: 'terraform', name: 'Terraform' },
      ].filter((t) => t.slug.startsWith(q.toLowerCase()))
    render(<Harness suggest={suggest} />)
    await user.type(screen.getByRole('combobox', { name: 'Stack' }), 't')
    expect(await screen.findByRole('option', { name: 'TypeScript' })).toBeVisible()
    await user.keyboard('{ArrowDown}{Enter}')
    expect(screen.getByRole('status')).toHaveTextContent('Terraform')
  })
})
