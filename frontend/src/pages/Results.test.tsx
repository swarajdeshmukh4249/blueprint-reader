import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import Results from '@/pages/Results'
import { useAnalysisStore } from '@/stores/useAnalysisStore'

describe('Results', () => {
  beforeEach(() => {
    useAnalysisStore.getState().reset()
  })

  it('shows empty state when no results exist', () => {
    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    )

    expect(screen.getByText(/no results yet/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /go to upload/i })).toBeInTheDocument()
  })
})
