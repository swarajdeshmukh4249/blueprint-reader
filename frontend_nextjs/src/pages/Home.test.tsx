import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import Home from '@/pages/Home'

describe('Home', () => {
  it('renders hero headline and primary CTA', () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
    )

    expect(screen.getByText('Blueprint')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /analyze a blueprint/i })).toBeInTheDocument()
  })
})
