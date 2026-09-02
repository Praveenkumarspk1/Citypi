import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Input } from './Input'

describe('Input', () => {
  it('renders input element', () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('applies size classes', () => {
    render(<Input size="sm" />)
    expect(screen.getByRole('textbox')).toHaveClass('px-3', 'py-1.5', 'text-sm')
    
    render(<Input size="md" />)
    expect(screen.getByRole('textbox')).toHaveClass('px-4', 'py-2', 'text-base')
    
    render(<Input size="lg" />)
    expect(screen.getByRole('textbox')).toHaveClass('px-4', 'py-3', 'text-lg')
  })

  it('shows error state', () => {
    render(<Input error="This field is required" />)
    expect(screen.getByRole('textbox')).toHaveClass('border-red-500')
    expect(screen.getByText('This field is required')).toBeInTheDocument()
  })

  it('shows label', () => {
    render(<Input label="Email" />)
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('calls onChange handler', () => {
    const handleChange = vi.fn()
    render(<Input onChange={handleChange} />)
    
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } })
    expect(handleChange).toHaveBeenCalledTimes(1)
  })

  it('applies disabled state', () => {
    render(<Input disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('renders left icon', () => {
    render(
      <Input leftIcon={<span data-testid="left-icon">@</span>} />
    )
    expect(screen.getByTestId('left-icon')).toBeInTheDocument()
  })

  it('renders right icon', () => {
    render(
      <Input rightIcon={<span data-testid="right-icon">🔍</span>} />
    )
    expect(screen.getByTestId('right-icon')).toBeInTheDocument()
  })

  it('applies full width class', () => {
    render(<Input fullWidth />)
    expect(screen.getByRole('textbox')).toHaveClass('w-full')
  })
})