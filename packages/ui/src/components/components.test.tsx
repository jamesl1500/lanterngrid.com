import { render, screen } from '@testing-library/react'

import { Avatar, initials } from './avatar'
import { Button } from './button'
import { KindBadge } from './kind-badge'
import { Tag } from './tag'

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
